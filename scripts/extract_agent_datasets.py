import os
import sys
import csv
from pathlib import Path

# Add src to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from q_learning_agent import QLearningAgent
import traci

def run_extraction():
    base_dir = Path(r"C:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic")
    os.chdir(base_dir)
    
    output_dir = "collected_data/agent_runs"
    os.makedirs(output_dir, exist_ok=True)
    
    agent = QLearningAgent()
    if os.path.exists("src/q_table.json"):
        agent.load_q_table("src/q_table.json")
    
    agent.epsilon = 0.0  # Frozen evaluation mode
    
    scenarios = [
        ("sumofiles/routes/s1_low_200.rou.xml", "metrics_agent_cars_200total_s1.csv"),
        ("sumofiles/routes/s2_medium_600.rou.xml", "metrics_agent_cars_600total_s2.csv"),
        ("sumofiles/routes/s3_heavy_asym_1200.rou.xml", "metrics_agent_cars_1200total_s3_asym.csv"),
        ("sumofiles/routes/s4_heavy_sym_1200.rou.xml", "metrics_agent_cars_1200total_s4_sym.csv")
    ]
    
    headers = [
        "step",
        "simulation_time",
        "action_duration",
        "we_waiting_time",
        "ns_waiting_time",
        "total_waiting_time",
        "we_green_duration",
        "ns_green_duration",
        "we_queue_length",
        "ns_queue_length",
        "total_queue_length",
        "throughput_completed",
        "throughput_rate",
        "normalized_W_q",
        "normalized_Q_q",
        "normalized_T_q",
        "starvation_penalty",
        "total_reward"
    ]
    
    print("Starting data extraction...")
    
    for scenario_path, out_filename in scenarios:
        out_filepath = os.path.join(output_dir, out_filename)
        
        sumo_cmd = ["sumo", "-n", "sumofiles/Traci.net.xml", "-r", scenario_path, "--no-warnings"]
        traci.start(sumo_cmd)
        
        decision_step = 0
        
        we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
        state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
        
        with open(out_filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            while traci.simulation.getMinExpectedNumber() > 0:
                action_idx = agent.get_action(state, evaluate=True)
                
                arrived, steps = agent.run_cycle(action_idx)
                
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
                    
                sim_time = traci.simulation.getTime()
                
                we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
                next_state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
                
                T = arrived / steps if steps > 0 else 0
                
                W_q = agent._normalize(total_wait, agent.bounds["W_min"], agent.bounds["W_max"], invert=True)
                Q_q = agent._normalize(total_queue, agent.bounds["Q_min"], agent.bounds["Q_max"], invert=True)
                T_q = agent._normalize(T, agent.bounds["T_min"], agent.bounds["T_max"], invert=False)
                P_s = 2.0 if (we_max_wait > 100.0 or ns_max_wait > 100.0) else 0.0
                
                reward = 0.50 * W_q + 0.30 * T_q + 0.20 * Q_q - P_s
                
                writer.writerow([
                    decision_step,
                    f"{sim_time:.1f}",
                    steps,
                    f"{we_max_wait:.2f}",
                    f"{ns_max_wait:.2f}",
                    f"{total_wait:.2f}",
                    agent.actions[action_idx][0],
                    agent.actions[action_idx][1],
                    we_queue,
                    ns_queue,
                    total_queue,
                    arrived,
                    f"{T:.4f}",
                    f"{W_q:.4f}",
                    f"{Q_q:.4f}",
                    f"{T_q:.4f}",
                    f"{P_s:.1f}",
                    f"{reward:.4f}"
                ])
                
                decision_step += 1
                state = next_state
                
        traci.close()
        
        # Verify row count
        with open(out_filepath, "r") as f:
            row_count = sum(1 for _ in f) - 1 # exclude header
            print(f"Generated {out_filepath}: {row_count} rows")

if __name__ == '__main__':
    run_extraction()
