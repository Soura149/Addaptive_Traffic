# Step 1: Add modules to provide access to specific libraries, functions, and data handling
import os       # Provides functions to handle file paths, directories, and environment variables
import sys      # Provides access to Python-specific system parameters and functions
import csv      # Used to format, generate, and write data directly into CSV files
import math     # Provides mathematical functions
import argparse # Used to parse command-line arguments (e.g. --train, --test-only)
import random   # Used for generating random numbers (epsilon-greedy exploration)
import json     # Used for saving the Q-table to a JSON file

# Step 2: Establish path to SUMO (SUMO_HOME)
# This ensures that Python knows where to find the TraCI library bundled with SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Add TraCI module to control the simulation programmatically
import traci

# Step 4: Define Current Configuration Variables
# --- CONFIGURABLE PARAMETERS ---

# These are the possible green light durations the agent can choose from
ACTIONS = [10, 20, 30, 45] 

# Reward Weights (dictate how much importance the agent places on each metric)
WT_WEIGHT = 0.50     # 50% penalty on wait time
TP_WEIGHT = 0.30     # 30% reward on throughput
QUEUE_WEIGHT = 0.20  # 20% penalty on queue length

# Normalization Scales (used to keep reward values roughly between -1 and 1)
# Adjust these based on typical max values observed in your specific simulation
WT_NORMALIZATION_SCALE = 100.0
TP_NORMALIZATION_SCALE = 10.0
QUEUE_NORMALIZATION_SCALE = 20.0

# Starvation configuration (prevents one direction from waiting indefinitely)
STARVATION_THRESHOLD = 100.0        # If wait time exceeds 100s...
STARVATION_PENALTY_MAGNITUDE = 2.0  # ...apply a massive penalty of 2.0 to the reward

# Q-learning Parameters (controls how the agent learns over time)
ALPHA = 0.1             # Learning rate: How much new information overrides old information (0 to 1)
GAMMA = 0.9             # Discount factor: Importance of future rewards vs immediate rewards (0 to 1)
EPSILON_START = 1.0     # Initial exploration rate: 100% chance to take a random action at the start
EPSILON_MIN = 0.05      # Minimum exploration rate: Agent will always have at least 5% chance to explore
EPSILON_DECAY = 0.995   # Decay rate per episode: Slowly reduces randomness as the agent learns

# Environmental Constants (Identify the specific lanes we are measuring)
LANE_WEST_EAST = "E0_0"
LANE_NORTH_SOUTH = "E1_0"


# Step 5: Define the Traffic Environment Class
# This class handles all direct interactions with the SUMO simulation
class TrafficEnvironment:
    def __init__(self, ui=False, config_file=None):
        self.ui = ui
        # Make the path absolute so the script can be run from outside the sumofiles folder
        if config_file:
            self.sumo_cfg_path = config_file
        else:
            self.sumo_cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Traci.sumocfg')
        self.cumulative_throughput = 0
        
    def start(self):
        self.cumulative_throughput = 0
        # Starts the simulation either with or without the GUI
        cmd = 'sumo-gui' if self.ui else 'sumo'
        self.sumo_config = [
            cmd,
            '-c', self.sumo_cfg_path,
            '--step-length', '1.0',
            '--waiting-time-memory', '10000', # Ensure SUMO remembers waiting time for vehicles stopped a long time
            '--no-warnings'                   # Suppress unnecessary console warnings
        ]
        traci.start(self.sumo_config)
        
    def stop(self):
        # Cleanly disconnects TraCI from the SUMO instance
        traci.close()

    def get_metrics(self):
        """
        Extracts current traffic metrics (queues and waiting times) from the simulation.
        Returns a dictionary containing these values.
        """
        # 1. Extract Queue Lengths (vehicles moving slower than 0.1 m/s)
        q_we = traci.lane.getLastStepHaltingNumber(LANE_WEST_EAST)
        q_ns = traci.lane.getLastStepHaltingNumber(LANE_NORTH_SOUTH)
        
        # 2. Extract Total Waiting Time for all vehicles on the lane
        wait_time_we = traci.lane.getWaitingTime(LANE_WEST_EAST)
        wait_time_ns = traci.lane.getWaitingTime(LANE_NORTH_SOUTH)
        
        # 3. Extract Number of Active Vehicles to compute the average wait time
        active_vehicles_we = traci.lane.getLastStepVehicleNumber(LANE_WEST_EAST)
        active_vehicles_ns = traci.lane.getLastStepVehicleNumber(LANE_NORTH_SOUTH)
        
        # Calculate Average Waiting Time (prevent division by zero)
        avg_waiting_time_we = wait_time_we / active_vehicles_we if active_vehicles_we > 0 else 0.0
        avg_waiting_time_ns = wait_time_ns / active_vehicles_ns if active_vehicles_ns > 0 else 0.0
        
        return {
            'q_we': q_we,
            'q_ns': q_ns,
            'wt_we': avg_waiting_time_we,
            'wt_ns': avg_waiting_time_ns
        }

    def apply_action_and_step(self, action_duration):
        """
        Applies the green duration for both directions and advances the simulation.
        A full cycle consists of: WE Green + WE Yellow (3s) + NS Green + NS Yellow (3s)
        Updates the cumulative throughput.
        """
        # Grab the traffic light logic for junction J2
        logics = traci.trafficlight.getAllProgramLogics("J2")
        logic = logics[0]
        
        # Phase 0 is West-East Green, Phase 2 is North-South Green
        logic.phases[0].duration = action_duration
        logic.phases[2].duration = action_duration
        
        # Apply the updated durations to the simulation
        traci.trafficlight.setProgramLogic("J2", logic)
        
        # Force traffic light to restart cycle from Phase 0 immediately
        traci.trafficlight.setPhase("J2", 0)
        
        # Calculate the total number of seconds (steps) this entire cycle will take
        total_steps = action_duration * 2 + 6
        
        # Step the simulation forward one second at a time for the duration of the cycle
        for _ in range(total_steps):
            if traci.simulation.getMinExpectedNumber() <= 0:
                break # Exit early if all cars have left the simulation
            traci.simulationStep()
            
            # Continuously accumulate how many cars reached their destination during this cycle
            self.cumulative_throughput += traci.simulation.getArrivedNumber()


# Step 6: Define the Q-Learning Agent Class
# This handles the brain of the RL agent (state mapping, action selection, and Q-table updates)
class QLearningAgent:
    def __init__(self):
        self.q_table = {}           # Dictionary to hold State -> Action Values
        self.epsilon = EPSILON_START # Starts with high exploration
        
    def get_state(self, metrics):
        """
        Converts raw numerical metrics into a discrete state string.
        Format: <WT_Level>_<Queue_Level>_<Starvation_Status>
        """
        # 1. Total Waiting-Time Condition
        total_waiting_time = metrics['wt_we'] + metrics['wt_ns']
        if total_waiting_time < 20:
            wt_level = "Low"
        elif total_waiting_time < 50:
            wt_level = "Medium"
        else:
            wt_level = "High"
            
        # 2. Total Queue Condition
        # Thresholds: < 5 (light), 5-15 (moderate), >= 15 (heavy)
        total_queue = metrics['q_we'] + metrics['q_ns']
        if total_queue < 5:
            queue_level = "Low"
        elif total_queue < 15:
            queue_level = "Medium"
        else:
            queue_level = "High"
            
        # 3. Starvation Status
        we_starving = metrics['wt_we'] > STARVATION_THRESHOLD
        ns_starving = metrics['wt_ns'] > STARVATION_THRESHOLD
        
        if we_starving and ns_starving:
            starv_status = "Both_Starving"
        elif we_starving:
            starv_status = "WE_Starving"
        elif ns_starving:
            starv_status = "NS_Starving"
        else:
            starv_status = "NoStarvation"
            
        return f"{wt_level}*{queue_level}*{starv_status}"

    def get_action(self, state):
        """
        Selects an action based on the Epsilon-Greedy strategy.
        """
        # Explore: Pick a random action
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(ACTIONS)
        
        # Exploit: Pick the best known action from the Q-table
        # Initialize state if it's never been seen before
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in ACTIONS}
        
        # Return the action with the highest Q-value
        return max(self.q_table[state], key=self.q_table[state].get)
        
    def update_q_value(self, state, action, reward, next_state):
        """
        Updates the Q-table using the standard Q-learning formula (Bellman equation).
        """
        # Ensure states exist in the dictionary to avoid KeyError
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in ACTIONS}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in ACTIONS}
            
        # Get the highest possible Q-value in the upcoming state
        max_next_q = max(self.q_table[next_state].values())
        
        # Get the current Q-value for the action we just took
        current_q = self.q_table[state][action]
        
        # --- Q-LEARNING FORMULA ---
        # New Q = Current Q + LearningRate * (Reward + DiscountFactor * MaxNextQ - Current Q)
        new_q = current_q + ALPHA * (reward + GAMMA * max_next_q - current_q)
        
        # Save the updated value back into the table
        self.q_table[state][action] = new_q
        
        return current_q, new_q

    def decay_epsilon(self):
        """
        Gradually reduces the exploration rate so the agent exploits more over time.
        """
        if self.epsilon > EPSILON_MIN:
            self.epsilon *= EPSILON_DECAY


# Step 7: Define the Exact Reward Calculation
def calculate_reward(old_metrics, new_metrics, cumulative_throughput_before, cumulative_throughput_after, action_duration):
    """
    Computes the final reward based on absolute metrics.
    """
    # 1. Wait Time Metric
    new_total_wait = new_metrics['wt_we'] + new_metrics['wt_ns']
    normalized_wait = new_total_wait / WT_NORMALIZATION_SCALE
    wait_contribution = -WT_WEIGHT * normalized_wait
    
    # 2. Queue Length Metric
    new_total_queue = new_metrics['q_we'] + new_metrics['q_ns']
    normalized_queue = new_total_queue / QUEUE_NORMALIZATION_SCALE
    queue_contribution = -QUEUE_WEIGHT * normalized_queue
    
    # 3. Throughput Metric
    vehicles_completed_during_transition = cumulative_throughput_after - cumulative_throughput_before
    transition_duration = 2 * action_duration + 6
    throughput_rate = vehicles_completed_during_transition / transition_duration
    
    normalized_throughput = throughput_rate / TP_NORMALIZATION_SCALE
    throughput_contribution = TP_WEIGHT * normalized_throughput
    
    # 4. Starvation Penalty
    starvation_penalty = 0.0
    if new_metrics['wt_we'] > STARVATION_THRESHOLD or new_metrics['wt_ns'] > STARVATION_THRESHOLD:
        starvation_penalty = STARVATION_PENALTY_MAGNITUDE
        
    # --- FINAL COMBINED REWARD ---
    reward = wait_contribution + queue_contribution + throughput_contribution - starvation_penalty
    
    return {
        'normalized_wait': normalized_wait,
        'normalized_queue': normalized_queue,
        'normalized_throughput': normalized_throughput,
        'wait_contribution': wait_contribution,
        'queue_contribution': queue_contribution,
        'throughput_contribution': throughput_contribution,
        'starvation_penalty': starvation_penalty,
        'reward': reward,
        'old_total_wait': old_metrics['wt_we'] + old_metrics['wt_ns'],
        'new_total_wait': new_total_wait,
        'old_total_queue': old_metrics['q_we'] + old_metrics['q_ns'],
        'new_total_queue': new_total_queue,
        'vehicles_completed_during_transition': vehicles_completed_during_transition,
        'transition_duration': transition_duration,
        'throughput_rate': throughput_rate
    }


# Step 8: Define the Debugging Test Mode
def run_test_mode():
    print("--- RUNNING TEST EPISODE BEFORE FULL TRAINING ---")
    env = TrafficEnvironment(ui=False)
    agent = QLearningAgent()
    agent.epsilon = 1.0 # Force exploration for random action
    
    env.start()
    
    # Run 50 dummy steps to let cars spawn
    for _ in range(50):
        traci.simulationStep()
        
    old_metrics = env.get_metrics()
    state = agent.get_state(old_metrics)
    action = agent.get_action(state)
    
    cumulative_throughput_before = env.cumulative_throughput
    
    # Apply action, run cycle, and get new state metrics
    env.apply_action_and_step(action)
    cumulative_throughput_after = env.cumulative_throughput
    new_metrics = env.get_metrics()
    next_state = agent.get_state(new_metrics)
    
    # Calculate exact reward
    result = calculate_reward(old_metrics, new_metrics, cumulative_throughput_before, cumulative_throughput_after, action)
    
    # Update Q-table
    q_before, q_after = agent.update_q_value(state, action, result['reward'], next_state)
    
    # --- PRINT EXHAUSTIVE DEBUG LOG ---
    print("\n================ EXACT REWARD FUNCTION VALIDATION ================")
    print(f"Previous State: {state}")
    print(f"Action:         {action}s (Transition Duration: {result['transition_duration']}s)")
    print(f"New State:      {next_state}\n")
    
    print(f"WT before: WE={old_metrics['wt_we']:.2f}, NS={old_metrics['wt_ns']:.2f} (Total: {result['old_total_wait']:.2f})")
    print(f"WT after:  WE={new_metrics['wt_we']:.2f}, NS={new_metrics['wt_ns']:.2f} (Total: {result['new_total_wait']:.2f})\n")
    
    print(f"Queue before: WE={old_metrics['q_we']}, NS={old_metrics['q_ns']} (Total: {result['old_total_queue']})")
    print(f"Queue after:  WE={new_metrics['q_we']}, NS={new_metrics['q_ns']} (Total: {result['new_total_queue']})\n")
    
    print(f"Throughput before action (Cumulative): {cumulative_throughput_before}")
    print(f"Throughput after action (Cumulative):  {cumulative_throughput_after}")
    print(f"Vehicles completed during transition:  {result['vehicles_completed_during_transition']}")
    print(f"Throughput rate:                       {result['throughput_rate']:.4f} vehicles/sec\n")
    
    print(f"Normalized Wait:       {result['normalized_wait']:.4f}  -> Contribution: {result['wait_contribution']:.4f}")
    print(f"Normalized Queue:      {result['normalized_queue']:.4f}  -> Contribution: {result['queue_contribution']:.4f}")
    print(f"Normalized Throughput: {result['normalized_throughput']:.4f}  -> Contribution: {result['throughput_contribution']:.4f}")
    print(f"Starvation penalty:    {result['starvation_penalty']:.4f}\n")
    
    print(f"Final Reward: {result['reward']:.4f}\n")
    
    print(f"Q-value before: {q_before:.4f}")
    print(f"Q-value after:  {q_after:.4f}")
    print("==================================================================\n")
    
    env.stop()
    print("Test run complete. Please review the output above.")


# Helper function to save every decision variable cleanly to CSV
def log_decision(csv_writer, ep, decision, sim_time, state, action, next_state, res, q_before, q_after, epsilon):
    csv_writer.writerow([
        ep, decision, sim_time, state, action, next_state,
        round(res['old_total_wait'], 2), round(res['new_total_wait'], 2),
        res['old_total_queue'], res['new_total_queue'],
        res['vehicles_completed_during_transition'], round(res['throughput_rate'], 4),
        round(res['normalized_wait'], 4), round(res['normalized_queue'], 4), round(res['normalized_throughput'], 4),
        round(res['wait_contribution'], 4), round(res['queue_contribution'], 4), round(res['throughput_contribution'], 4),
        round(res['starvation_penalty'], 4), round(res['reward'], 4),
        round(q_before, 4), round(q_after, 4), round(epsilon, 4), res['transition_duration']
    ])


# Step 9: Define the Full Training Loop
def run_training(episodes, config_file=None):
    print(f"--- RUNNING FULL TRAINING FOR {episodes} EPISODES ---")
    env = TrafficEnvironment(ui=False, config_file=config_file)
    agent = QLearningAgent()
    
    # Open CSV file and write the precise header row
    log_file = open("main_1200_decision_log.csv", "w", newline="")
    csv_writer = csv.writer(log_file)
    csv_writer.writerow([
        "episode", "decision", "simulation_time", "state", "action", "next_state",
        "we_waiting_time", "ns_waiting_time", "total_waiting_time",
        "we_queue", "ns_queue", "total_queue",
        "throughput_during_transition", "throughput_rate",
        "normalized_wait", "normalized_queue", "normalized_throughput",
        "wait_contribution", "queue_contribution", "throughput_contribution",
        "starvation_penalty", "reward",
        "q_value_before", "q_value_after", "epsilon", "transition_duration"
    ])
    
    summary_file = open("main_1200_training_episode_summary.csv", "w", newline="")
    summary_writer = csv.writer(summary_file)
    summary_writer.writerow([
        "episode", "total_reward", "average_reward", "average_waiting_time", "average_queue",
        "total_throughput", "throughput_rate", "starvation_events", "number_of_decisions", "epsilon",
        "action_10_count", "action_20_count", "action_30_count", "action_45_count"
    ])
    
    episode_rewards = []
    MAX_SIM_TIME = 3600  # Safety threshold to prevent infinite episode loops
    
    for ep in range(1, episodes + 1):
        env.start()
        
        ep_reward = 0
        decision = 0
        ep_total_wait = 0
        ep_total_queue = 0
        ep_we_wait = 0
        ep_ns_wait = 0
        ep_we_queue = 0
        ep_ns_queue = 0
        ep_starvation_events = 0
        ep_actions = {a: 0 for a in ACTIONS}
        
        for _ in range(50):
            traci.simulationStep()
            
        old_metrics = env.get_metrics()
        state = agent.get_state(old_metrics)
        
        while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < MAX_SIM_TIME:
            action = agent.get_action(state)
            
            cumulative_throughput_before = env.cumulative_throughput
            env.apply_action_and_step(action)
            cumulative_throughput_after = env.cumulative_throughput
            
            new_metrics = env.get_metrics()
            next_state = agent.get_state(new_metrics)
            
            res = calculate_reward(old_metrics, new_metrics, cumulative_throughput_before, cumulative_throughput_after, action)
            
            q_before, q_after = agent.update_q_value(state, action, res['reward'], next_state)
            
            sim_time = traci.simulation.getTime()
            if not is_sensitivity:
                log_decision(csv_writer, ep, decision, sim_time, state, action, next_state, res, q_before, q_after, agent.epsilon)
            
            ep_reward += res['reward']
            decision += 1
            ep_total_wait += res['new_total_wait']
            ep_total_queue += res['new_total_queue']
            ep_we_wait += new_metrics['wt_we']
            ep_ns_wait += new_metrics['wt_ns']
            ep_we_queue += new_metrics['q_we']
            ep_ns_queue += new_metrics['q_ns']
            if new_metrics['wt_we'] > STARVATION_THRESHOLD or new_metrics['wt_ns'] > STARVATION_THRESHOLD:
                ep_starvation_events += 1
            ep_actions[action] += 1
            
            state = next_state
            old_metrics = new_metrics
            
        total_throughput = env.cumulative_throughput
        end_time = traci.simulation.getTime()
        env.stop()
        agent.decay_epsilon() 
        
        episode_rewards.append(ep_reward)
        avg_wait = ep_total_wait / decision if decision > 0 else 0
        avg_queue = ep_total_queue / decision if decision > 0 else 0
        avg_reward = ep_reward / decision if decision > 0 else 0
        throughput_rate_ep = total_throughput / end_time if end_time > 0 else 0
        
        print(f"\n--- Episode {ep} Summary ---")
        print(f"Total Reward:      {ep_reward:.2f}")
        print(f"Avg Reward:        {avg_reward:.2f}")
        print(f"Total Decisions:   {decision}")
        print(f"Avg Wait / Cycle:  {avg_wait:.2f}")
        print(f"Avg Queue / Cycle: {avg_queue:.2f}")
        print(f"Total Throughput:  {total_throughput}")
        print(f"Starvation Events: {ep_starvation_events}")
        print(f"Actions Selected:  {ep_actions}")
        print(f"Epsilon at end:    {agent.epsilon:.3f}\n")
        
        summary_writer.writerow([
            ep, round(ep_reward, 2), round(avg_reward, 2), round(avg_wait, 2), round(avg_queue, 2),
            total_throughput, round(throughput_rate_ep, 4), ep_starvation_events, decision, round(agent.epsilon, 3),
            ep_actions[10], ep_actions[20], ep_actions[30], ep_actions[45]
        ])
        
    log_file.close() 
    summary_file.close()
    
    print("\n--- FINAL LEARNED POLICY ---")
    with open("main_1200_q_table.json", "w") as f:
        json.dump(agent.q_table, f, indent=4)
        
    for state, actions in agent.q_table.items():
        best_action = max(actions, key=actions.get)
        print(f"{state} -> {best_action} seconds")
    
    print("\nTraining completed. Q-table saved to 'main_1200_q_table.json' and logs to 'main_1200_decision_log.csv'.")


def run_evaluation(episodes, config_file=None, is_sensitivity=False):
    print(f"--- RUNNING EVALUATION FOR {episodes} EPISODES ---")
    env = TrafficEnvironment(ui=False, config_file=config_file)
    agent = QLearningAgent()
    
    agent.epsilon = 0.0
    try:
        with open("main_1200_q_table.json", "r") as f:
            raw_q_table = json.load(f)
            agent.q_table = {s: {int(a): v for a, v in actions.items()} for s, actions in raw_q_table.items()}
        print("Successfully loaded main_1200_q_table.json")
    except FileNotFoundError:
        print("Warning: main_1200_q_table.json not found. Evaluating with empty Q-table.")
        
    if not is_sensitivity:
        log_file = open("main_1200_evaluation_log.csv", "w", newline="")
        csv_writer = csv.writer(log_file)
        csv_writer.writerow([
            "episode", "decision", "simulation_time", "state", "action", "next_state",
            "we_waiting_time", "ns_waiting_time", "total_waiting_time",
            "we_queue", "ns_queue", "total_queue",
            "throughput_during_transition", "throughput_rate",
            "normalized_wait", "normalized_queue", "normalized_throughput",
            "wait_contribution", "queue_contribution", "throughput_contribution",
            "starvation_penalty", "reward",
            "q_value_before", "q_value_after", "epsilon", "transition_duration"
        ])
    else:
        csv_writer = None
    
    MAX_SIM_TIME = 3600
    for ep in range(1, episodes + 1):
        env.start()
        
        ep_reward = 0
        decision = 0
        ep_total_wait = 0
        ep_total_queue = 0
        ep_we_wait = 0
        ep_ns_wait = 0
        ep_we_queue = 0
        ep_ns_queue = 0
        ep_starvation_events = 0
        ep_actions = {a: 0 for a in ACTIONS}
        
        for _ in range(50):
            traci.simulationStep()
            
        old_metrics = env.get_metrics()
        state = agent.get_state(old_metrics)
        
        while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < MAX_SIM_TIME:
            action = agent.get_action(state)
            
            cumulative_throughput_before = env.cumulative_throughput
            env.apply_action_and_step(action)
            cumulative_throughput_after = env.cumulative_throughput
            
            new_metrics = env.get_metrics()
            next_state = agent.get_state(new_metrics)
            
            res = calculate_reward(old_metrics, new_metrics, cumulative_throughput_before, cumulative_throughput_after, action)
            
            q_before = agent.q_table.get(state, {}).get(action, 0.0)
            q_after = q_before 
            
            sim_time = traci.simulation.getTime()
            if not is_sensitivity:
                log_decision(csv_writer, ep, decision, sim_time, state, action, next_state, res, q_before, q_after, agent.epsilon)
            
            ep_reward += res['reward']
            decision += 1
            ep_total_wait += res['new_total_wait']
            ep_total_queue += res['new_total_queue']
            ep_we_wait += new_metrics['wt_we']
            ep_ns_wait += new_metrics['wt_ns']
            ep_we_queue += new_metrics['q_we']
            ep_ns_queue += new_metrics['q_ns']
            if new_metrics['wt_we'] > STARVATION_THRESHOLD or new_metrics['wt_ns'] > STARVATION_THRESHOLD:
                ep_starvation_events += 1
            ep_actions[action] += 1
            
            state = next_state
            old_metrics = new_metrics
            
        total_throughput = env.cumulative_throughput
        env.stop()
        
        avg_wait = ep_total_wait / decision if decision > 0 else 0
        avg_queue = ep_total_queue / decision if decision > 0 else 0
        
        print(f"\n--- Evaluation Episode {ep} Summary ---")
        print(f"Total Reward:      {ep_reward:.2f}")
        print(f"Total Decisions:   {decision}")
        print(f"Avg Wait / Cycle:  {avg_wait:.2f}")
        print(f"Avg Queue / Cycle: {avg_queue:.2f}")
        print(f"Total Throughput:  {total_throughput}")
        print(f"Starvation Events: {ep_starvation_events}")
        print(f"Actions Selected:  {ep_actions}\n")
        
        if is_sensitivity:
            return {
                "throughput": total_throughput,
                "avg_wait": avg_wait,
                "avg_queue": avg_queue,
                "we_wait": ep_we_wait / decision if decision > 0 else 0,
                "ns_wait": ep_ns_wait / decision if decision > 0 else 0,
                "we_queue": ep_we_queue / decision if decision > 0 else 0,
                "ns_queue": ep_ns_queue / decision if decision > 0 else 0,
                "starvation": ep_starvation_events,
                "reward": ep_reward
            }
        
    if not is_sensitivity:
        log_file.close() 
        print("\nEvaluation completed. Logs saved to 'main_1200_evaluation_log.csv'.")


# Step 10: Define Baseline Evaluation
def run_baseline(fixed_duration, config_file=None):
    print(f"\n--- RUNNING BASELINE EVALUATION: {fixed_duration}s ---")
    env = TrafficEnvironment(ui=False, config_file=config_file)
    env.start()
    
    total_waiting_time = 0
    total_queue = 0
    starvation_events = 0
    steps = 0
    MAX_SIM_TIME = 3600
    
    for _ in range(50):
        traci.simulationStep()
        
    env.apply_action_and_step(fixed_duration)
    
    while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < MAX_SIM_TIME:
        env.apply_action_and_step(fixed_duration)
        metrics = env.get_metrics()
        
        total_waiting_time += (metrics['wt_we'] + metrics['wt_ns'])
        total_queue += (metrics['q_we'] + metrics['q_ns'])
        
        if metrics['wt_we'] > STARVATION_THRESHOLD or metrics['wt_ns'] > STARVATION_THRESHOLD:
            starvation_events += 1
            
        steps += 1
        
    total_throughput = env.cumulative_throughput
    env.stop()
    
    avg_waiting_time = total_waiting_time / steps if steps > 0 else 0
    avg_queue = total_queue / steps if steps > 0 else 0
    
    print(f"Baseline {fixed_duration}s:")
    print(f"  Total Throughput: {total_throughput}")
    print(f"  Avg Total Waiting Time per Cycle: {avg_waiting_time:.2f}")
    print(f"  Avg Total Queue per Cycle: {avg_queue:.2f}")
    print(f"  Starvation Events: {starvation_events}")
    
    # Write to main_1200_baseline_results.csv
    file_exists = os.path.isfile("main_1200_baseline_results.csv")
    with open("main_1200_baseline_results.csv", "a", newline="") as bf:
        writer = csv.writer(bf)
        if not file_exists:
            writer.writerow(["duration", "total_throughput", "avg_waiting_time", "avg_queue", "starvation_events"])
        writer.writerow([fixed_duration, total_throughput, round(avg_waiting_time, 2), round(avg_queue, 2), starvation_events])
        
    return total_throughput, avg_waiting_time


def run_sensitivity_experiment():
    print("\n--- RUNNING TRAFFIC-CONDITION SENSITIVITY EXPERIMENT ---")
    conditions = [
        {"name": "Original", "we": 900, "ns": 300},
        {"name": "Balanced", "we": 600, "ns": 600},
        {"name": "WE-Heavy", "we": 1000, "ns": 200},
        {"name": "NS-Heavy", "we": 300, "ns": 900}
    ]
    
    out_file = "traffic_condition_experiments.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["experiment_name", "we_vehicles", "ns_vehicles", "total_vehicles", 
                         "throughput", "avg_waiting_time", "avg_queue", 
                         "we_waiting_time", "ns_waiting_time", "we_queue", "ns_queue", 
                         "starvation_events", "total_reward"])
        
        for cond in conditions:
            print(f"\nEvaluating Condition: {cond['name']} (WE:{cond['we']} NS:{cond['ns']})")
            
            route_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <vType id="car" maxSpeed="13.89" length="4.7"/>
    <flow id="flow_west_east" type="car" from="E0" to="E0.58" begin="0.00" end="1000.00" number="{cond['we']}" departLane="0"/>
    <flow id="flow_north_south" type="car" from="E1" to="E2" begin="0.00" end="1000.00" number="{cond['ns']}" departLane="0"/>
</routes>"""
            with open("Sensitivity.rou.xml", "w") as rf:
                rf.write(route_content)
                
            cfg_content = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="Traci.net.xml"/>
        <route-files value="Sensitivity.rou.xml"/>
    </input>
</configuration>"""
            with open("Sensitivity.sumocfg", "w") as cf:
                cf.write(cfg_content)
                
            res = run_evaluation(1, config_file="Sensitivity.sumocfg", is_sensitivity=True)
            
            total_veh = cond['we'] + cond['ns']
            writer.writerow([
                cond['name'], cond['we'], cond['ns'], total_veh,
                res['throughput'], round(res['avg_wait'], 2), round(res['avg_queue'], 2),
                round(res['we_wait'], 2), round(res['ns_wait'], 2), 
                round(res['we_queue'], 2), round(res['ns_queue'], 2),
                res['starvation'], round(res['reward'], 2)
            ])
            print(f"Done -> Throughput: {res['throughput']} | Wait: {res['avg_wait']:.2f}")

    print(f"\nExperiment complete. Results saved to {out_file}")

# Step 11: Main Execution Block
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Q-Learning Traffic Light Agent")
    # Define acceptable command line arguments
    parser.add_argument('--test-only', action='store_true', help="Run a single step validation and exit")
    parser.add_argument('--train', type=int, help="Run full training for N episodes")
    parser.add_argument('--evaluate', type=int, help="Run evaluation for N episodes using saved Q-table")
    parser.add_argument('--baseline', action='store_true', help="Run fixed duration baselines")
    parser.add_argument('--sensitivity', action='store_true', help="Run traffic condition sensitivity experiment")
    parser.add_argument('--config', type=str, default=None, help="Path to the SUMO config file (.sumocfg)")
    
    args = parser.parse_args()
    
    if args.test_only:
        run_test_mode()
    elif args.train:
        run_training(args.train, args.config)
    elif args.evaluate:
        run_evaluation(args.evaluate, args.config)
    elif args.sensitivity:
        run_sensitivity_experiment()
    elif args.baseline:
        baseline_file = "main_1200_baseline_results.csv"
        if os.path.exists(baseline_file):
            os.remove(baseline_file)
        for dur in [10, 20, 30, 45]:
            run_baseline(dur, args.config)
    else:
        print("Please specify --test-only, --train N, --evaluate N, or --baseline")
