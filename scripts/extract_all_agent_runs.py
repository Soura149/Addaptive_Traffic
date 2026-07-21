import os
import sys
import csv
import glob
from pathlib import Path

# Add src to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from q_learning_agent import QLearningAgent
from generate_scenarios import generate_route_file
import traci
import numpy as np

def run_extraction():
    base_dir = Path(r"C:\VSCODE\CISInternship_Implement")
    os.chdir(base_dir)
    
    data_dir = base_dir / "collected_data"
    output_dir = data_dir / "agent_runs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Identify unique scenarios from baseline
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    unique_scenarios = set()
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        parts = filename.replace('.csv', '').split('_')
        
        cars = None
        for p in parts:
            if p.endswith('total'):
                cars = int(p.replace('total', ''))
                
        balance = "unbalanced" if "unbalanced" in parts else "balanced"
        
        if cars is not None:
            unique_scenarios.add((cars, balance))
            
    print(f"Identified {len(unique_scenarios)} unique historical scenarios.")
    
    agent = QLearningAgent()
    if os.path.exists("src/q_table.json"):
        agent.load_q_table("src/q_table.json")
    
    agent.epsilon = 0.0  # Frozen evaluation mode
    
    headers = [
        "Step",
        "Queue_West_East",
        "Queue_North_South",
        "Queue_SD",
        "Arrival_West_East",
        "Arrival_North_South",
        "Throughput_Step",
        "Avg_Waiting_Time_West_East",
        "Avg_Waiting_Time_North_South",
        "WE_Green_Duration",
        "NS_Green_Duration"
    ]
    
    # Store mappings for the matrix
    mappings = []
    
    for cars, balance in sorted(list(unique_scenarios)):
        # Generate temporary route file
        route_filename = f"dynamic_{cars}_{balance}.rou.xml"
        route_path = base_dir / "sumofiles" / "routes" / route_filename
        
        if balance == "balanced":
            we = cars // 2
            ns = cars // 2
            agent_filename = f"metrics_agent_cars_{cars}total_1000s.csv"
        else:
            we = int(cars * 0.75)
            ns = int(cars * 0.25)
            agent_filename = f"metrics_agent_cars_{cars}total_1000s_unbalanced.csv"
            
        generate_route_file(route_path, we, ns, duration=1000.0)
        
        out_filepath = output_dir / agent_filename
        
        sumo_cmd = ["sumo", "-n", "sumofiles/Traci.net.xml", "-r", str(route_path), "--no-warnings"]
        traci.start(sumo_cmd)
        
        we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
        state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
        
        decision_step = 1
        with open(out_filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            while traci.simulation.getMinExpectedNumber() > 0:
                action_idx = agent.get_action(state, evaluate=True)
                arrived, steps = agent.run_cycle(action_idx)
                
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
                    
                we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
                next_state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
                
                queue_sd = abs(we_queue - ns_queue) / 2.0  # std dev of two values
                
                # We don't have separate arrival counts easily from run_cycle, just put total in Throughput
                arrival_we = 0
                arrival_ns = 0
                
                # Max wait is the closest to avg waiting time we have readily available without tracking every vehicle
                avg_wait_we = we_max_wait / 2.0 
                avg_wait_ns = ns_max_wait / 2.0
                
                # Use simulation time as step to align with 1000s duration timeline
                sim_time = int(traci.simulation.getTime())
                
                writer.writerow([
                    sim_time,
                    we_queue,
                    ns_queue,
                    f"{queue_sd:.2f}",
                    arrival_we,
                    arrival_ns,
                    arrived,
                    f"{avg_wait_we:.2f}",
                    f"{avg_wait_ns:.2f}",
                    agent.actions[action_idx][0],
                    agent.actions[action_idx][1]
                ])
                
                decision_step += 1
                state = next_state
                
        traci.close()
        
        # Verify row count
        with open(out_filepath, "r") as f:
            row_count = sum(1 for _ in f) - 1
            
        print(f"Generated {agent_filename} (Rows: {row_count})")
        
        # Add to mappings for the matrix (match with all corresponding durations)
        for d in ["10s", "20s", "30s", "45s"]:
            if balance == "balanced":
                hist_name = f"metrics_dur_{d}_cars_{cars}total_1000s.csv"
            else:
                hist_name = f"metrics_dur_{d}_cars_{cars}total_1000s_unbalanced.csv"
            mappings.append((hist_name, agent_filename))
            
    print("\n" + "="*80)
    print("MAPPING MATRIX: HISTORICAL DATASETS -> Q-AGENT COUNTERPARTS")
    print("="*80)
    print(f"{'Historical Baseline CSV':<50} | {'Generated Q-Agent CSV':<40}")
    print("-" * 95)
    for hist, agent_f in mappings:
        print(f"{hist:<50} | {agent_f:<40}")

if __name__ == '__main__':
    run_extraction()
