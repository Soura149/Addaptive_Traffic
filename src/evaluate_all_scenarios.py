import os
import json
import csv
import pandas as pd
import traci
from route_generator import generate_routes
from q_learning_agent import ACTION_SPACE, get_live_metrics, get_state, execute_action, DATA_DIR

def parse_baselines():
    baselines = {
        '10s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_10s.csv'),
        '20s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_20s.csv'),
        '30s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_30s.csv'),
        '45s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_45s.csv')
    }
    
    records = []
    for name, f in baselines.items():
        if not os.path.exists(f):
            print(f"Warning: {f} not found.")
            continue
        df = pd.read_csv(f)
        # Average waiting time across the steps
        avg_wait = (df['we_waiting_time'].mean() + df['ns_waiting_time'].mean()) / 2
        max_queue = max(df['we_queue'].max(), df['ns_queue'].max())
        throughput = df['completed_vehicles'].sum()
        
        records.append({
            'Scenario_Name': name,
            'Type': 'Fixed Baseline',
            'Traffic_Volume': 1200,
            'Avg_Waiting_Time': avg_wait,
            'Max_Queue': max_queue,
            'Cumulative_Throughput': throughput
        })
    return records

def run_agent_evaluation(volume, we_count, ns_count, balance_type="Unbalanced"):
    print(f"\nEvaluating Frozen Agent for {volume} vehicles ({we_count} WE, {ns_count} NS - {balance_type})...")
    generate_routes("Traci.rou.xml", episode_seed=volume, total_time=1000.0, we_count=we_count, ns_count=ns_count)
    
    try:
        with open(os.path.join(DATA_DIR, "q_table.json"), "r") as f:
            q_table = json.load(f)
    except FileNotFoundError:
        print("Error: q_table.json not found! Cannot evaluate.")
        return None
        
    traci.start(["sumo", "-c", "Traci.sumocfg", "--no-step-log", "true"])
    
    step = 0
    total_completed = 0
    max_we_queue = 0
    max_ns_queue = 0
    cumulative_waiting_time = 0
    
    # Initial State
    we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
    state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        # 1. Force Epsilon strictly to 0.0 (Exploitation Only)
        if state not in q_table:
            action = 0 
        else:
            action = q_table[state].index(max(q_table[state]))
            
        # Execute Transition
        completed_vehicles, _ = execute_action(action)
        total_completed += completed_vehicles
        
        # Observe Next State Metrics
        we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
        
        # Track metrics
        max_we_queue = max(max_we_queue, we_queue)
        max_ns_queue = max(max_ns_queue, ns_queue)
        cumulative_waiting_time += ((we_wait_sum + ns_wait_sum) / 2.0)
        
        # No Q-table update happens here (Learning Disabled)
        state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
        step += 1
        
        if step > 2000: # safety limit
            print("Safety timeout reached.")
            break
            
    traci.close()
    
    avg_waiting_time = cumulative_waiting_time / step if step > 0 else 0
    
    return {
        'Scenario_Name': f'Frozen Agent ({volume}v {balance_type})',
        'Type': 'RL Agent',
        'Traffic_Volume': volume,
        'Avg_Waiting_Time': avg_waiting_time,
        'Max_Queue': max(max_we_queue, max_ns_queue),
        'Cumulative_Throughput': total_completed
    }

def main():
    print("Phase 1: Parsing Legacy Baselines...")
    baseline_records = parse_baselines()
    
    print("\nPhase 2 & 3: Executing Agent Evaluations...")
    agent_records = []
    scenarios = [
        # Unbalanced (3:1 WE:NS)
        (200, 150, 50, "Unbalanced"),
        (400, 300, 100, "Unbalanced"),
        (800, 600, 200, "Unbalanced"),
        # Balanced (1:1 WE:NS)
        (200, 100, 100, "Balanced"),
        (400, 200, 200, "Balanced"),
        (800, 400, 400, "Balanced")
    ]
    
    for vol, we, ns, balance_type in scenarios:
        record = run_agent_evaluation(vol, we, ns, balance_type)
        if record:
            agent_records.append(record)
            
    print("\nPhase 4: Compiling Master Ledger...")
    all_records = baseline_records + agent_records
    df = pd.DataFrame(all_records)
    
    out_dir = DATA_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "master_generalization_ledger.csv")
    df.to_csv(out_path, index=False)
    
    print(f"\nMaster Ledger saved to {out_path}\n")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
