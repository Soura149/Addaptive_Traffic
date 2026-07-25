import os
import sys
import json
import csv

# Set up paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if WORKSPACE_DIR not in sys.path:
    sys.path.append(WORKSPACE_DIR)
sys.path.append(os.path.join(WORKSPACE_DIR, "src"))

from q_learning_agent import QLearningAgent
import traci
from sumolib import checkBinary

# ==========================================
# CONFIGURABLE PARAMETERS
# ==========================================
# Time to run the simulation (in seconds)
# e.g., 300 for 5 minutes, 600 for 10 minutes
SIMULATION_DURATION = 2000

# The scenario to run. Can be changed to other scenarios in sumofiles/routes/
SCENARIO_NAME = "s5_peak_1800.rou.xml" 

# Set to True to generate a new continuous route file matching SIMULATION_DURATION
GENERATE_CONTINUOUS_FLOW = True
# If True, randomly selects traffic probability for both lanes to create varied scenarios on each run
RANDOMIZE_PROBABILITIES = True
# If RANDOMIZE_PROBABILITIES is False, it uses these fixed values (0.3 = 30% chance per second):
WE_FLOW_PROBABILITY = 0.3
NS_FLOW_PROBABILITY = 0.3

# Enable Live Adaptation (allows agent to learn during evaluation)
LIVE_ADAPTATION = False
# ==========================================

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

OUTPUT_CSV_FILE = os.path.join(DATA_DIR, f"asymmetric_data_{SIMULATION_DURATION}s.csv")

def get_metrics():
    we_edges = ["E0"]
    ns_edges = ["E1"]
    we_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in we_edges)
    ns_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in ns_edges)
    we_w = sum(traci.edge.getWaitingTime(e) for e in we_edges)
    ns_w = sum(traci.edge.getWaitingTime(e) for e in ns_edges)
    return we_q, ns_q, we_w, ns_w

def generate_continuous_route(route_file_path, duration, prob_we, prob_ns):
    with open(route_file_path, "w") as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        f.write('    <vType id="car" maxSpeed="13.89" length="4.7"/>\n')
        f.write('    <route id="route_we" edges="E0 E0.58"/>\n')
        f.write('    <route id="route_ns" edges="E1 E2"/>\n')
        f.write(f'    <flow id="flow_we" type="car" route="route_we" begin="0" end="{duration}" probability="{prob_we}" departLane="0"/>\n')
        f.write(f'    <flow id="flow_ns" type="car" route="route_ns" begin="0" end="{duration}" probability="{prob_ns}" departLane="0"/>\n')
        f.write('</routes>\n')

def run_time_based_simulation():
    print(f"Starting time-based simulation for {SIMULATION_DURATION} seconds...")
    print(f"Scenario: {SCENARIO_NAME}")
    
    # Load Agent
    if LIVE_ADAPTATION:
        print("Live Adaptation ENABLED: Agent will learn and adapt in real-time.")
        agent = QLearningAgent(alpha=0.1, epsilon=0.05)
    else:
        print("Live Adaptation DISABLED: Agent will use strictly frozen Q-Table.")
        agent = QLearningAgent(alpha=0.0, epsilon=0.0)
        
    q_table_path = os.path.join(WORKSPACE_DIR, "outputs", "universal_q_table.json")
    if os.path.exists(q_table_path):
        with open(q_table_path, 'r') as f:
            agent.q_table = json.load(f)
        print("Loaded Q-Table successfully.")
    else:
        print(f"Warning: q_table.json not found at {q_table_path}. Running with empty Q-table.")

    route_path = os.path.join(WORKSPACE_DIR, "sumofiles", "routes", SCENARIO_NAME)
    
    if GENERATE_CONTINUOUS_FLOW:
        import random
        we_prob = WE_FLOW_PROBABILITY
        ns_prob = NS_FLOW_PROBABILITY
        
        if RANDOMIZE_PROBABILITIES:
            primary_prob = round(random.uniform(0.5, 0.8), 2)
            secondary_prob = round(random.uniform(0.05, 0.2), 2)
            # 50% chance WE is the busy lane, 50% chance NS is the busy lane
            if random.random() > 0.5:
                we_prob, ns_prob = primary_prob, secondary_prob
            else:
                we_prob, ns_prob = secondary_prob, primary_prob
            print(f"Randomized Asymmetric Traffic Flow -> WE: {int(we_prob*100)}%, NS: {int(ns_prob*100)}%")
        else:
            print(f"Fixed Asymmetric Traffic Flow -> WE: {int(we_prob*100)}%, NS: {int(ns_prob*100)}%")
            
        route_path = os.path.join(WORKSPACE_DIR, "sumofiles", "routes", "continuous_flow.rou.xml")
        generate_continuous_route(route_path, SIMULATION_DURATION, we_prob, ns_prob)
        print(f"Generated continuous flow route file at {route_path}")
        
    net_path = os.path.join(WORKSPACE_DIR, "sumofiles", "Traci.net.xml")
    
    cmd = [checkBinary('sumo'), "-n", net_path, "-r", route_path, "--no-step-log", "true", "--no-warnings", "true", "--time-to-teleport", "-1"]
    traci.start(cmd)

    current_phase = 0 # 0 for WE Green, 2 for NS Green
    
    # Open CSV for data collection
    with open(OUTPUT_CSV_FILE, mode='w', newline='') as csv_file:
        fieldnames = [
            'Sim_Time_s', 
            'Current_Phase', 
            'Phase_Duration_s', 
            'WE_Queue', 
            'NS_Queue', 
            'WE_WaitTime', 
            'NS_WaitTime', 
            'Total_Throughput'
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        total_throughput = 0
        
        # Run until SIMULATION_DURATION is reached
        while traci.simulation.getTime() < SIMULATION_DURATION:
            # Note: We do not break on getMinExpectedNumber() == 0 unless we really want to stop when all cars are gone.
            # But the user specifically wants it to run until the time finishes, so we keep going.
            
            we_q, ns_q, we_w, ns_w = get_metrics()
            state = agent.get_state(we_q, ns_q, we_w, ns_w)
            
            # Agent chooses action (green phase duration in seconds)
            action = agent.choose_action(state)
            
            # Set the phase to Green for the chosen direction
            traci.trafficlight.setPhase("J2", current_phase)
            
            phase_duration_spent = 0
            # Run simulation for the duration of the chosen action
            for _ in range(action):
                if traci.simulation.getTime() >= SIMULATION_DURATION:
                    break
                    
                traci.simulationStep()
                phase_duration_spent += 1
                total_throughput += traci.simulation.getArrivedNumber()
                
                # Log data at each second (or step)
                current_time = traci.simulation.getTime()
                c_we_q, c_ns_q, c_we_w, c_ns_w = get_metrics()
                
                # Determine phase name
                phase_name = 'WE_Green' if current_phase == 0 else 'NS_Green'
                
                writer.writerow({
                    'Sim_Time_s': current_time,
                    'Current_Phase': phase_name,
                    'Phase_Duration_s': phase_duration_spent,
                    'WE_Queue': c_we_q,
                    'NS_Queue': c_ns_q,
                    'WE_WaitTime': c_we_w,
                    'NS_WaitTime': c_ns_w,
                    'Total_Throughput': total_throughput
                })

            if traci.simulation.getTime() >= SIMULATION_DURATION:
                break

            # Transition phase (Yellow light)
            traci.trafficlight.setPhase("J2", current_phase + 1)
            yellow_duration_spent = 0
            
            # Yellow phase lasts 3 seconds
            for _ in range(3): 
                if traci.simulation.getTime() >= SIMULATION_DURATION:
                    break
                    
                traci.simulationStep()
                yellow_duration_spent += 1
                total_throughput += traci.simulation.getArrivedNumber()
                
                current_time = traci.simulation.getTime()
                c_we_q, c_ns_q, c_we_w, c_ns_w = get_metrics()
                
                phase_name = 'WE_Yellow' if current_phase == 0 else 'NS_Yellow'
                
                writer.writerow({
                    'Sim_Time_s': current_time,
                    'Current_Phase': phase_name,
                    'Phase_Duration_s': yellow_duration_spent,
                    'WE_Queue': c_we_q,
                    'NS_Queue': c_ns_q,
                    'WE_WaitTime': c_we_w,
                    'NS_WaitTime': c_ns_w,
                    'Total_Throughput': total_throughput
                })

            # Switch phase for next iteration
            current_phase = 2 if current_phase == 0 else 0

    end_time = traci.simulation.getTime()
    traci.close()
    print(f"Simulation completed at time {end_time}s.")
    print(f"Data saved to {OUTPUT_CSV_FILE}")

if __name__ == "__main__":
    run_time_based_simulation()
