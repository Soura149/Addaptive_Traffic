import os
import json
import csv
import random
import time
import traci

# Q-Learning parameters
ALPHA = 0.1
GAMMA = 0.99
EPSILON = 1.0
EPSILON_MIN = 0.01
EPSILON_DECAY = 0.995

# 2. Asymmetric Action Space
# Explicit combination mapping independent Green times for West-East (WE) and North-South (NS)
ACTION_SPACE = [
    (10, 10), # Action 0
    (20, 10), # Action 1
    (30, 10), # Action 2
    (45, 10), # Action 3
    (10, 20), # Action 4
    (20, 20), # Action 5
    (30, 20), # Action 6
    (45, 20)  # Action 7
]

def clear_contamination():
    """1. Contamination Reset: Programmatically delete old instances to ensure clean run."""
    files_to_remove = ["q_table.json", "decision_log.csv", "training_episode_summary.csv"]
    for f in files_to_remove:
        if os.path.exists(f):
            os.remove(f)
            print(f"Removed old {f}")

def get_live_metrics():
    """Extract real-time metrics using TraCI."""
    # Edges E0 (WE) and E1 (NS)
    we_vehs = traci.edge.getLastStepVehicleIDs("E0")
    ns_vehs = traci.edge.getLastStepVehicleIDs("E1")
    
    we_wait_sum = sum(traci.vehicle.getWaitingTime(v) for v in we_vehs)
    ns_wait_sum = sum(traci.vehicle.getWaitingTime(v) for v in ns_vehs)
    
    we_max_wait = max([traci.vehicle.getWaitingTime(v) for v in we_vehs]) if we_vehs else 0.0
    ns_max_wait = max([traci.vehicle.getWaitingTime(v) for v in ns_vehs]) if ns_vehs else 0.0
    
    we_queue = traci.edge.getLastStepHaltingNumber("E0")
    ns_queue = traci.edge.getLastStepHaltingNumber("E1")
    
    return we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue

def get_state(we_max_wait, ns_max_wait, we_queue, ns_queue):
    """
    3. Live Data Extraction & State Space: Discretize values into 18 states.
    - WE/NS Queue: Low (<5)=0, Medium (5-15)=1, High (>=15)=2
    - Starvation: NoStarvation (both wait <= 100)=0, Starving (either wait > 100)=1
    """
    def discretize_queue(q):
        if q < 5: return 0
        if q <= 15: return 1
        return 2

    we_q_level = discretize_queue(we_queue)
    ns_q_level = discretize_queue(ns_queue)
    
    starving = 1 if (we_max_wait > 100.0 or ns_max_wait > 100.0) else 0
    
    # State is a string representation of the tuple to be used as JSON key
    return f"{we_q_level}_{ns_q_level}_{starving}"

def execute_action(action_index):
    we_green, ns_green = ACTION_SPACE[action_index]
    yellow_duration = 3
    total_completed = 0
    
    # Run the cycle: WE Green -> WE Yellow -> NS Green -> NS Yellow
    phases = [
        (0, we_green),       # Phase 0: GGrr
        (1, yellow_duration),# Phase 1: yyrr
        (2, ns_green),       # Phase 2: rrGG
        (3, yellow_duration) # Phase 3: rryy
    ]
    
    for phase_idx, duration in phases:
        traci.trafficlight.setPhase("J2", phase_idx)
        for _ in range(duration):
            traci.simulationStep()
            total_completed += traci.simulation.getArrivedNumber()
            
    transition_duration = we_green + ns_green + 2 * yellow_duration
    return total_completed, transition_duration

def run_episode(episode, q_table, epsilon=1.0, learning=True, log_file="decision_log.csv"):
    # Start SUMO
    traci.start(["sumo", "-c", "Traci.sumocfg", "--no-step-log", "true"])
    
    # Prepare logs for this episode if needed, but decision log spans the run
    decision_log_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline='') as f:
        writer = csv.writer(f)
        if not decision_log_exists:
            # 5. Robust Logging Columns
            writer.writerow(["episode", "timestamp", "state", "action", "we_green", "ns_green", 
                             "we_waiting_time", "ns_waiting_time", "we_queue", "ns_queue", "reward"])
            
        step = 0
        total_reward = 0
        
        # Initial State
        we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
        state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
        
        while traci.simulation.getMinExpectedNumber() > 0:
            # Select action
            if state not in q_table:
                q_table[state] = [0.0 for _ in range(8)]
                
            if random.random() < epsilon:
                action = random.randint(0, 7)
            else:
                # Argmax
                action = q_table[state].index(max(q_table[state]))
                
            we_green, ns_green = ACTION_SPACE[action]
            
            # Execute transition
            completed_vehicles, transition_dur = execute_action(action)
            
            # Observe next state metrics
            we_wait_sum, ns_wait_sum, we_max_wait, ns_max_wait, we_queue, ns_queue = get_live_metrics()
            next_state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
            
            # 4. Absolute-State Reward Function
            total_waiting_time = we_wait_sum + ns_wait_sum
            total_queue = we_queue + ns_queue
            throughput_rate = completed_vehicles / transition_dur if transition_dur > 0 else 0.0
            starvation_penalty = 2.0 if (we_max_wait > 100.0 or ns_max_wait > 100.0) else 0.0
            
            reward = (-0.5 * (total_waiting_time / 100.0) 
                      - 0.2 * (total_queue / 20.0) 
                      + 0.3 * (throughput_rate / 10.0) 
                      - starvation_penalty)
            
            # Q-learning update
            if next_state not in q_table:
                q_table[next_state] = [0.0 for _ in range(8)]
                
            if learning:
                best_next_q = max(q_table[next_state])
                q_table[state][action] = q_table[state][action] + ALPHA * (reward + GAMMA * best_next_q - q_table[state][action])
            
            # Log transition
            timestamp = traci.simulation.getTime()
            writer.writerow([episode, timestamp, state, action, we_green, ns_green, 
                             we_wait_sum, ns_wait_sum, we_queue, ns_queue, reward])
            
            state = next_state
            total_reward += reward
            step += 1
            
            if step >= 100: # Limit steps per episode for safety during tests
                break

    traci.close()
    
    # Save Q-table
    with open("q_table.json", "w") as f:
        json.dump(q_table, f, indent=4)
        
    return total_reward

if __name__ == "__main__":
    clear_contamination()
    
    q_table = {}
    episodes = 5
    
    with open("training_episode_summary.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["episode", "total_reward", "epsilon"])
        
    for ep in range(episodes):
        total_r = run_episode(ep, q_table)
        print(f"Episode {ep} finished. Total Reward: {total_r:.2f}, Epsilon: {EPSILON:.3f}")
        
        with open("training_episode_summary.csv", "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([ep, total_r, EPSILON])
            
        EPSILON = max(EPSILON_MIN, EPSILON * EPSILON_DECAY)

    print("Training finished.")
