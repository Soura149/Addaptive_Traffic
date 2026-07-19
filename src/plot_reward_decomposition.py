import os
import json
import traci
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from route_generator import generate_routes
from q_learning_agent import get_live_metrics, get_state, execute_action, ACTION_SPACE

DATA_DIR = os.path.join(os.path.dirname(__file__), "new_experiment_analytics")

def get_reward_decomposition():
    print("Running RL Agent for 1200v Asymmetric to generate dynamic reward decomposition...")
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
    wait_penalties = []
    queue_penalties = []
    throughput_rewards = []
    starvation_penalties = []
    total_rewards = []
    
    step = 0
    
    we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
    state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        if state not in q_table:
            action = 0 
        else:
            action = q_table[state].index(max(q_table[state]))
            
        completed_vehicles, _ = execute_action(action)
        
        we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
        
        # Calculate transition duration just like training
        we_green, ns_green = ACTION_SPACE[action]
        transition_dur = we_green + ns_green + 6 # 6 is for the two 3-second yellow phases
        
        # Exact reward formulas from q_learning_agent.py
        total_waiting_time = we_wait_sum + ns_wait_sum
        total_queue = we_queue + ns_queue
        throughput_rate = completed_vehicles / transition_dur if transition_dur > 0 else 0.0
        
        wait_penalty = -0.5 * (total_waiting_time / 100.0)
        queue_penalty = -0.2 * (total_queue / 20.0)
        throughput_reward = 0.3 * (throughput_rate / 10.0)
        starvation_penalty = -2.0 if (we_max_wait > 100.0 or ns_max_wait > 100.0) else 0.0
        
        total_reward = wait_penalty + queue_penalty + throughput_reward + starvation_penalty
        
        step += 1
        steps.append(step)
        wait_penalties.append(wait_penalty)
        queue_penalties.append(queue_penalty)
        throughput_rewards.append(throughput_reward)
        starvation_penalties.append(starvation_penalty)
        total_rewards.append(total_reward)
        
        state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
        
        if step > 3000: # Safety fallback
            break
            
    traci.close()
    
    return pd.DataFrame({
        'Step': steps,
        'Waiting Time Penalty': wait_penalties,
        'Queue Length Penalty': queue_penalties,
        'Throughput Reward': throughput_rewards,
        'Starvation Penalty': starvation_penalties,
        'Total Combined Reward': total_rewards
    })

def main():
    df = get_reward_decomposition()
    
    # Melt the dataframe so we can plot multiple lines using Seaborn easily
    df_melted = df.melt(id_vars=['Step'], var_name='Reward Component', value_name='Score')
    
    print("Rendering Reward Function Decomposition Timeline...")
    sns.set_theme(style="darkgrid")
    plt.figure(figsize=(14, 8), dpi=300)
    
    # Custom color palette mapping
    palette = {
        'Waiting Time Penalty': '#e74c3c', # Red
        'Queue Length Penalty': '#e67e22', # Orange
        'Throughput Reward': '#2ecc71',    # Green
        'Starvation Penalty': '#9b59b6',   # Purple
        'Total Combined Reward': '#2c3e50' # Dark Blue/Black
    }
    
    sns.lineplot(
        data=df_melted, 
        x='Step', 
        y='Score', 
        hue='Reward Component', 
        palette=palette,
        linewidth=2
    )
    
    # Highlight the Total Combined Reward line to make it thicker
    ax = plt.gca()
    for line in ax.lines:
        if line.get_label() == 'Total Combined Reward':
            line.set_linewidth(4)
            line.set_linestyle('--')
    
    plt.title("Dynamic Reward Function Decomposition (1200v Asymmetric Evaluation)", fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Simulation Time Steps", fontsize=14)
    plt.ylabel("Reward Component Score", fontsize=14)
    
    plt.legend(title='Component', fontsize=12, title_fontsize=13, loc='lower left')
    
    # Add a horizontal zero line for reference
    plt.axhline(0, color='black', linewidth=1, linestyle='-', alpha=0.5)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, "reward_function_decomposition.png")
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Decomposition chart successfully saved to {out_path}")

if __name__ == "__main__":
    main()
