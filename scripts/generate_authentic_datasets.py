import os
import sys
import csv
from pathlib import Path

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_DIR, "src"))

from q_learning_agent import QLearningAgent
from generate_scenarios import generate_route_file
import traci
from sumolib import checkBinary
import json

def generate_authentic_datasets():
    os.chdir(WORKSPACE_DIR)
    
    output_dir = os.path.join(WORKSPACE_DIR, "collected_data", "agent_runs")
    os.makedirs(output_dir, exist_ok=True)
    
    agent = QLearningAgent(alpha=0.0, epsilon=0.0)
    q_table_path = os.path.join(WORKSPACE_DIR, "outputs", "q_table.json")
    
    if os.path.exists(q_table_path):
        with open(q_table_path, 'r') as f:
            agent.q_table = json.load(f)
        print("Loaded Q-Table successfully.")
    else:
        print("CRITICAL: outputs/q_table.json not found! Cannot evaluate.")
        sys.exit(1)
        
    volumes = [200, 400, 600, 800, 1200]
    balances = ["balanced", "unbalanced"]
    
    headers = [
        "Step",
        "Queue_West_East",
        "Queue_North_South",
        "Throughput_Step",
        "Avg_Waiting_Time_West_East",
        "Avg_Waiting_Time_North_South"
    ]
    
    for cars in volumes:
        for balance in balances:
            print(f"Generating authentic dataset for {cars} cars ({balance})...")
            
            # Generate route
            route_filename = f"dynamic_{cars}_{balance}.rou.xml"
            route_path = os.path.join(WORKSPACE_DIR, "sumofiles", "routes", route_filename)
            
            if balance == "balanced":
                we = cars // 2
                ns = cars // 2
                agent_filename = f"metrics_agent_cars_{cars}total_1000s.csv"
            else:
                we = int(cars * 0.75)
                ns = int(cars * 0.25)
                agent_filename = f"metrics_agent_cars_{cars}total_1000s_unbalanced.csv"
                
            generate_route_file(f"dynamic_{cars}_{balance}", {"we": we, "ns": ns})
            
            out_filepath = os.path.join(output_dir, agent_filename)
            
            net_path = os.path.join(WORKSPACE_DIR, "sumofiles", "Traci.net.xml")
            sumo_cmd = [checkBinary('sumo'), "-n", net_path, "-r", route_path, "--no-warnings", "true", "--no-step-log", "true", "--time-to-teleport", "-1"]
            traci.start(sumo_cmd)
            
            we_edges = ["E0"]
            ns_edges = ["E1"]
            
            def get_metrics():
                we_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in we_edges)
                ns_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in ns_edges)
                we_w = sum(traci.edge.getWaitingTime(e) for e in we_edges)
                ns_w = sum(traci.edge.getWaitingTime(e) for e in ns_edges)
                return we_q, ns_q, we_q + ns_q, we_w, ns_w, we_w + ns_w
                
            current_phase = 0
            we_q, ns_q, t_q, we_w, ns_w, t_w = get_metrics()
            
            with open(out_filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                step_idx = 0
                
                while traci.simulation.getMinExpectedNumber() > 0:
                    state = agent.get_state(we_q, ns_q, we_w, ns_w)
                    action = agent.choose_action(state)
                    
                    traci.trafficlight.setPhase("J2", current_phase)
                    
                    arrived = 0
                    for _ in range(action):
                        traci.simulationStep()
                        arrived += traci.simulation.getArrivedNumber()
                        if traci.simulation.getMinExpectedNumber() == 0:
                            break
                            
                    # Get metrics after green phase
                    next_we_q, next_ns_q, next_t_q, next_we_w, next_ns_w, next_t_w = get_metrics()
                    
                    writer.writerow([
                        step_idx,
                        next_we_q,
                        next_ns_q,
                        arrived,
                        next_we_w / max(1, next_we_q), # Rough avg per vehicle in queue
                        next_ns_w / max(1, next_ns_q)  # Rough avg per vehicle in queue
                    ])
                    
                    we_q, ns_q, t_q, we_w, ns_w, t_w = next_we_q, next_ns_q, next_t_q, next_we_w, next_ns_w, next_t_w
                    step_idx += 1
                    
                    if traci.simulation.getMinExpectedNumber() == 0:
                        break
                        
                    traci.trafficlight.setPhase("J2", current_phase + 1)
                    for _ in range(3):
                        traci.simulationStep()
                        if traci.simulation.getMinExpectedNumber() == 0:
                            break
                            
                    current_phase = 2 if current_phase == 0 else 0
                    
            traci.close()
            print(f"Generated {out_filepath}")

if __name__ == '__main__':
    generate_authentic_datasets()
