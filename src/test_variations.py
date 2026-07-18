import json
import csv
import traci
from route_generator import generate_routes
from q_learning_agent import ACTION_SPACE, get_live_metrics, get_state, execute_action

def run_evaluation(volume, we_count, ns_count, output_file):
    print(f"Running evaluation for {volume} vehicles ({we_count} WE, {ns_count} NS)...")
    # Generate the variation profile
    generate_routes("Traci.rou.xml", episode_seed=volume, total_time=1000.0, we_count=we_count, ns_count=ns_count)
    
    # Load frozen Q-table
    try:
        with open("q_table.json", "r") as f:
            q_table = json.load(f)
    except FileNotFoundError:
        print("Error: q_table.json not found! Cannot evaluate.")
        return
        
    traci.start(["sumo", "-c", "Traci.sumocfg", "--no-step-log", "true"])
    
    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["step", "we_waiting_time", "ns_waiting_time", "we_queue", "ns_queue", "completed_throughput", "max_we_queue", "max_ns_queue"])
        
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
                # If an unseen state is encountered, pick an arbitrary safe action (e.g. Action 0)
                action = 0 
            else:
                action = q_table[state].index(max(q_table[state]))
                
            # Execute Transition
            completed_vehicles, _ = execute_action(action)
            total_completed += completed_vehicles
            
            # Observe Next State Metrics
            we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
            
            # 4. Meticulously track requested metrics
            max_we_queue = max(max_we_queue, we_queue)
            max_ns_queue = max(max_ns_queue, ns_queue)
            cumulative_waiting_time += (we_wait_sum + ns_wait_sum)
            
            writer.writerow([step, we_wait_sum, ns_wait_sum, we_queue, ns_queue, completed_vehicles, max_we_queue, max_ns_queue])
            
            # No Q-table update happens here (Learning Disabled)
            state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
            step += 1
            
            if step > 250: # safety limit to prevent infinite loops if deadlocked
                break
                
    traci.close()
    
    avg_waiting_time = cumulative_waiting_time / step if step > 0 else 0
    print(f"--- Results for {volume} Vehicles ---")
    print(f"Total Throughput: {total_completed}")
    print(f"Avg Cumulative Wait Time: {avg_waiting_time:.2f}s")
    print(f"Max Directional Queue - WE: {max_we_queue}, NS: {max_ns_queue}\n")
    return total_completed, avg_waiting_time, max_we_queue, max_ns_queue

def main():
    # Maintain the 3:1 (WE:NS) asymmetric ratio
    variations = [
        (200, 150, 50, "eval_variation_200.csv"),
        (400, 300, 100, "eval_variation_400.csv"),
        (800, 600, 200, "eval_variation_800.csv")
    ]
    
    for vol, we, ns, out_file in variations:
        run_evaluation(vol, we, ns, out_file)

if __name__ == "__main__":
    main()
