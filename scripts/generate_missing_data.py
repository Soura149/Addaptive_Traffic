import os
import sys
import json
import csv
import numpy as np
import re

base_dir = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"
sys.path.append(base_dir)

from src.q_learning_agent import QLearningAgent

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
from sumolib import checkBinary

def generate_agent_metrics():
    print("Generating agent metrics...")
    agent = QLearningAgent(alpha=0.0, epsilon=0.0)
    
    # Load Q-table
    if os.path.exists(agent.q_table_path):
        with open(agent.q_table_path, 'r') as f:
            agent.q_table = json.load(f)
        print("Loaded frozen Q-table.")
    
    volumes = [200, 400, 600, 800, 1200]
    balances = ["balanced", "unbalanced"]
    
    sumo_binary = checkBinary('sumo')
    net_path = os.path.join(base_dir, "sumofiles", "Traci.net.xml")
    
    for vol in volumes:
        for balance in balances:
            scenario_name = f"dynamic_{vol}_{balance}.rou.xml"
            route_path = os.path.join(base_dir, "sumofiles", "routes", scenario_name)
            
            suffix = "_unbalanced" if balance == "unbalanced" else ""
            out_filename = f"metrics_agent_cars_{vol}total_1000s{suffix}.csv"
            out_path = os.path.join(base_dir, "collected_data", out_filename)
            
            if not os.path.exists(route_path):
                print(f"Skipping {route_path} (not found)")
                continue
                
            cmd = [sumo_binary, "-n", net_path, "-r", route_path, "--no-step-log", "true", "--no-warnings", "true", "--time-to-teleport", "-1"]
            traci.start(cmd)
            
            with open(out_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Step", "Queue_West_East", "Queue_North_South", "Queue_SD", "Arrival_West_East", "Arrival_North_South", "Throughput_Step", "Avg_Waiting_Time_West_East", "Avg_Waiting_Time_North_South"])
                
                step = 0
                current_phase = 0
                
                def record_step():
                    nonlocal step
                    step += 1
                    we_q = traci.edge.getLastStepHaltingNumber("E0")
                    ns_q = traci.edge.getLastStepHaltingNumber("E1")
                    we_w = traci.edge.getWaitingTime("E0")
                    ns_w = traci.edge.getWaitingTime("E1")
                    q_sd = np.std([we_q, ns_q])
                    thr = traci.simulation.getArrivedNumber()
                    writer.writerow([step, we_q, ns_q, q_sd, 0, 0, thr, we_w, ns_w])
                
                # initial state
                we_q = traci.edge.getLastStepHaltingNumber("E0")
                ns_q = traci.edge.getLastStepHaltingNumber("E1")
                we_w = traci.edge.getWaitingTime("E0")
                ns_w = traci.edge.getWaitingTime("E1")
                state = agent.get_state(we_q if current_phase==0 else ns_q, 
                                      ns_q if current_phase==0 else we_q, 
                                      we_w if current_phase==0 else ns_w, 
                                      ns_w if current_phase==0 else we_w)
                
                while traci.simulation.getMinExpectedNumber() > 0:
                    action = agent.choose_action(state)
                    
                    traci.trafficlight.setPhase("J2", current_phase)
                    for _ in range(action):
                        traci.simulationStep()
                        record_step()
                        if traci.simulation.getMinExpectedNumber() == 0: break
                        
                    if traci.simulation.getMinExpectedNumber() == 0: break
                    
                    # Yellow
                    traci.trafficlight.setPhase("J2", current_phase + 1)
                    for _ in range(3):
                        traci.simulationStep()
                        record_step()
                        if traci.simulation.getMinExpectedNumber() == 0: break
                        
                    if traci.simulation.getMinExpectedNumber() == 0: break
                    
                    current_phase = 2 if current_phase == 0 else 0
                    
                    we_q = traci.edge.getLastStepHaltingNumber("E0")
                    ns_q = traci.edge.getLastStepHaltingNumber("E1")
                    we_w = traci.edge.getWaitingTime("E0")
                    ns_w = traci.edge.getWaitingTime("E1")
                    state = agent.get_state(we_q if current_phase==0 else ns_q, 
                                          ns_q if current_phase==0 else we_q, 
                                          we_w if current_phase==0 else ns_w, 
                                          ns_w if current_phase==0 else we_w)
                                          
            traci.close()
            print(f"Generated {out_path}")

def generate_training_data():
    summary_path = os.path.join(base_dir, "outputs", "training_summary.csv")
    if not os.path.exists(summary_path):
        print("No training summary found")
        return
        
    vol_data = {}
    with open(summary_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenario = row['scenario']
            m = re.search(r"route_we_(\d+)_ns_(\d+)\.rou\.xml", scenario)
            if m:
                vol = int(m.group(1)) + int(m.group(2))
                if vol not in vol_data:
                    vol_data[vol] = []
                vol_data[vol].append(row)
                
    for vol, rows in vol_data.items():
        out_path = os.path.join(base_dir, "collected_data", f"training_vol_{vol}.csv")
        with open(out_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Generated {out_path}")

if __name__ == "__main__":
    generate_agent_metrics()
    generate_training_data()
