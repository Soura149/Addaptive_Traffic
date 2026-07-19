import os
import json
import traci
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from route_generator import generate_routes
from q_learning_agent import get_live_metrics, get_state, execute_action

DATA_DIR = os.path.join(os.path.dirname(__file__), "new_experiment_analytics")

def get_agent_throughput():
    print("Running RL Agent for 1200v Asymmetric to generate real-time throughput data...")
    generate_routes(
        os.path.join(os.path.dirname(__file__), "Traci.rou.xml"), 
        episode_seed=1200, 
        total_time=1000.0, 
        we_count=900, 
        ns_count=300
    )
    
    q_table_path = os.path.join(DATA_DIR, "q_table.json")
    with open(q_table_path, 'r') as f:
        q_table = json.load(f)
        
    sumo_cfg = os.path.join(os.path.dirname(__file__), "Traci.sumocfg")
    traci.start(["sumo", "-c", sumo_cfg, "--no-step-log", "true"])
    
    steps = []
    cumulative_throughput = []
    
    step = 0
    total_completed = 0
    
    # Run the loop to collect metrics dynamically
    we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
    state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        if state not in q_table:
            action = 0 
        else:
            action = q_table[state].index(max(q_table[state]))
            
        completed_vehicles, _ = execute_action(action)
        total_completed += completed_vehicles
        
        we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
        state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
        
        step += 1
        steps.append(step)
        cumulative_throughput.append(total_completed)
        
        if step > 3000: # Safety fallback
            break
            
    traci.close()
    
    return pd.DataFrame({'Step': steps, 'Cumulative_Throughput': cumulative_throughput, 'Model': 'RL Agent'})

def main():
    baselines = [
        ('10s', r"..\collected_data\metrics_dur_10s_cars_1200total_1000s_unbalanced.csv"),
        ('20s', r"..\collected_data\metrics_dur_20s_cars_1200total_1000s_unbalanced.csv"),
        ('30s', r"..\collected_data\metrics_dur_30s_cars_1200total_1000s_unbalanced.csv"),
        ('45s', r"..\collected_data\metrics_dur_45s_cars_1200total_1000s_unbalanced.csv"),
    ]
    
    dfs = []
    print("Parsing static baseline throughput data...")
    for label, rel_path in baselines:
        p = os.path.join(os.path.dirname(__file__), rel_path)
        if os.path.exists(p):
            df = pd.read_csv(p)
            df['Cumulative_Throughput'] = df['Throughput_Step'].cumsum()
            df['Model'] = f"Fixed {label}"
            dfs.append(df[['Step', 'Cumulative_Throughput', 'Model']])
        else:
            print(f"Warning: Baseline data {p} not found.")
            
    # Dynamically evaluate the RL agent
    dfs.append(get_agent_throughput())
    
    final_df = pd.concat(dfs, ignore_index=True)
    
    print("Rendering Throughput Evolution Chart...")
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(14, 8), dpi=300)
    
    # Plotting continuous time-series lines
    sns.lineplot(
        data=final_df, 
        x='Step', 
        y='Cumulative_Throughput', 
        hue='Model', 
        palette='Set1',
        linewidth=3
    )
    
    plt.title("Dynamic Throughput Accumulation Over Time (1200v Asymmetric)", fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Simulation Time Steps", fontsize=14)
    plt.ylabel("Cumulative Completed Vehicles", fontsize=14)
    
    plt.legend(title='Control Algorithm', fontsize=12, title_fontsize=13, loc='upper left')
    
    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, "throughput_evolution_timeline.png")
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Chart successfully saved to {out_path}")

if __name__ == "__main__":
    main()
