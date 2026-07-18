import os
import csv
import traci
from route_generator import generate_routes as generate_dynamic_route
from q_learning_agent import run_episode, clear_contamination, get_live_metrics

def run_fixed_time_baseline(duration, seed, output_file):
    print(f"Starting Fixed Baseline: {duration}s with seed {seed}")
    # Inject vehicle arrival patterns for baseline
    generate_dynamic_route("Traci.rou.xml", seed)
    traci.start(["sumo", "-c", "Traci.sumocfg", "--no-step-log", "true"])
    
    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["cycle_step", "we_waiting_time", "ns_waiting_time", "we_queue", "ns_queue", "completed_vehicles"])
        
        step = 0
        total_completed = 0
        
        # Loop until all vehicles have cleared
        while traci.simulation.getMinExpectedNumber() > 0:
            completed_in_cycle = 0
            
            # Phase 0: WE Green
            traci.trafficlight.setPhase("J2", 0)
            for _ in range(duration): 
                traci.simulationStep()
                completed_in_cycle += traci.simulation.getArrivedNumber()
            
            # Phase 1: WE Yellow
            traci.trafficlight.setPhase("J2", 1)
            for _ in range(3): 
                traci.simulationStep()
                completed_in_cycle += traci.simulation.getArrivedNumber()
            
            # Phase 2: NS Green
            traci.trafficlight.setPhase("J2", 2)
            for _ in range(duration): 
                traci.simulationStep()
                completed_in_cycle += traci.simulation.getArrivedNumber()
            
            # Phase 3: NS Yellow
            traci.trafficlight.setPhase("J2", 3)
            for _ in range(3): 
                traci.simulationStep()
                completed_in_cycle += traci.simulation.getArrivedNumber()
                
            we_wait_sum, ns_wait_sum, _, _, we_queue, ns_queue = get_live_metrics()
            writer.writerow([step, we_wait_sum, ns_wait_sum, we_queue, ns_queue, completed_in_cycle])
            total_completed += completed_in_cycle
            step += 1
            
            if step > 200: # Safety break just in case of deadlock
                print(f"Safety break triggered for {duration}s baseline.")
                break

    traci.close()
    print(f"Finished Fixed Baseline {duration}s. Total Completed: {total_completed}")

def main():
    # 1. Training Execution Loop
    clear_contamination()
    
    # Also clean evaluation log if it exists from previous runs
    if os.path.exists("evaluation_log.csv"):
        os.remove("evaluation_log.csv")
    
    q_table = {}
    episodes = 50
    start_epsilon = 1.0
    end_epsilon = 0.05
    
    print("=== Phase 1: Training ===")
    with open("training_episode_summary.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["episode", "total_reward", "epsilon"])
        
    for ep in range(episodes):
        generate_dynamic_route("Traci.rou.xml", ep)
        
        # Smooth linear decay
        epsilon = start_epsilon - ep * ((start_epsilon - end_epsilon) / max(1, episodes - 1))
        epsilon = max(end_epsilon, epsilon)
        
        total_r = run_episode(ep, q_table, epsilon=epsilon, learning=True, log_file="decision_log.csv")
        
        with open("training_episode_summary.csv", "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([ep, total_r, epsilon])
            
        print(f"Episode {ep} | Reward: {total_r:.2f} | Epsilon: {epsilon:.3f}")
        
    print("Training Complete. Policy saved to q_table.json.")
        
    # 2. Frozen Evaluation Mode
    print("\n=== Phase 2: Frozen Evaluation Mode ===")
    eval_seeds = [101, 102, 103, 104, 105]
    for idx, seed in enumerate(eval_seeds):
        generate_dynamic_route("Traci.rou.xml", seed)
        # Frozen: learning=False, epsilon=0.0
        total_r = run_episode(f"eval_{seed}", q_table, epsilon=0.0, learning=False, log_file="evaluation_log.csv")
        print(f"Eval Run {idx+1} (Seed {seed}) | Reward: {total_r:.2f}")

    # 3. Live Fixed-Time Baselines
    print("\n=== Phase 3: Fixed-Time Baselines ===")
    durations = [10, 20, 30, 45]
    baseline_seed = 42 # static seed for consistent baseline comparison
    
    for dur in durations:
        run_fixed_time_baseline(dur, baseline_seed, f"baseline_{dur}s.csv")
        
    print("\nAll experiments successfully completed.")

if __name__ == "__main__":
    main()
