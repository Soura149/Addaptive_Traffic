import os
import sys
import json
import csv

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

def evaluate_agent():
    print("Initializing Step 5: Evaluation and Benchmark...")
    
    agent = QLearningAgent(alpha=0.0, epsilon=0.0)
    
    # Load Q-table
    if os.path.exists(agent.q_table_path):
        with open(agent.q_table_path, 'r') as f:
            agent.q_table = json.load(f)
        print("Loaded frozen Q-table.")
    else:
        print("WARNING: Q-table not found, using empty Q-table!")

    scenarios = [
        ("Off-Peak Symmetric", "route_we_100_ns_100.rou.xml"),
        ("Moderate Symmetric", "route_we_600_ns_600.rou.xml"),
        ("Heavy WE Asymmetric", "route_we_900_ns_300.rou.xml"),
        ("Heavy NS Asymmetric", "route_we_300_ns_900.rou.xml"),
        ("Peak Gridlock", "route_we_1200_ns_1200.rou.xml")
    ]
    
    baselines = [(10, 10), (20, 20), (30, 30), (45, 45)]
    
    results = []
    
    sumo_binary = checkBinary('sumo')
    net_path = os.path.join(base_dir, "sumofiles", "Traci.net.xml")
    
    for scenario_name, filename in scenarios:
        route_path = os.path.join(base_dir, "sumofiles", "routes", filename)
        
        # Test 1: RL Agent
        # Test 2-5: Fixed Baselines
        evaluations = [("RL Agent", None)] + [(f"Fixed ({b[0]}s,{b[1]}s)", b) for b in baselines]
        
        for agent_name, fixed_action in evaluations:
            cmd = [sumo_binary, "-n", net_path, "-r", route_path, "--no-step-log", "true", "--no-warnings", "true", "--time-to-teleport", "-1"]
            traci.start(cmd)
            
            def get_metrics():
                we_q = traci.edge.getLastStepHaltingNumber("E0")
                ns_q = traci.edge.getLastStepHaltingNumber("E1")
                we_w = traci.edge.getWaitingTime("E0")
                ns_w = traci.edge.getWaitingTime("E1")
                return we_q, ns_q, we_w, ns_w
                
            step = 0
            total_throughput = 0
            sum_q = 0
            sum_w = 0
            decisions = 0
            starvation_events = 0
            
            we_q, ns_q, we_w, ns_w = get_metrics()
            state = agent.get_state(we_q, ns_q, we_w, ns_w)
            
            while traci.simulation.getMinExpectedNumber() > 0:
                if fixed_action is not None:
                    action_tuple = fixed_action
                else:
                    action_tuple = agent.choose_action(state)
                    
                a_WE, a_NS = action_tuple
                
                # Check starvation event at decision time
                if max(we_w, ns_w) > 100.0:
                    starvation_events += 1
                
                # Run WE Green
                traci.trafficlight.setPhase("J2", 0)
                for _ in range(a_WE):
                    traci.simulationStep()
                    total_throughput += traci.simulation.getArrivedNumber()
                    if traci.simulation.getMinExpectedNumber() == 0: break
                if traci.simulation.getMinExpectedNumber() == 0: break
                
                # Run WE Yellow
                traci.trafficlight.setPhase("J2", 1)
                for _ in range(3):
                    traci.simulationStep()
                    total_throughput += traci.simulation.getArrivedNumber()
                    if traci.simulation.getMinExpectedNumber() == 0: break
                if traci.simulation.getMinExpectedNumber() == 0: break
                
                # Run NS Green
                traci.trafficlight.setPhase("J2", 2)
                for _ in range(a_NS):
                    traci.simulationStep()
                    total_throughput += traci.simulation.getArrivedNumber()
                    if traci.simulation.getMinExpectedNumber() == 0: break
                if traci.simulation.getMinExpectedNumber() == 0: break
                
                # Run NS Yellow
                traci.trafficlight.setPhase("J2", 3)
                for _ in range(3):
                    traci.simulationStep()
                    total_throughput += traci.simulation.getArrivedNumber()
                    if traci.simulation.getMinExpectedNumber() == 0: break
                if traci.simulation.getMinExpectedNumber() == 0: break
                
                # Record metrics for averages
                we_q, ns_q, we_w, ns_w = get_metrics()
                state = agent.get_state(we_q, ns_q, we_w, ns_w)
                
                sum_q += (we_q + ns_q)
                sum_w += (we_w + ns_w)
                decisions += 1
                
            traci.close()
            
            avg_q = sum_q / decisions if decisions > 0 else 0
            avg_w = sum_w / decisions if decisions > 0 else 0
            
            print(f"[{scenario_name}] {agent_name} -> Thr: {total_throughput}, AvgW: {avg_w:.2f}, AvgQ: {avg_q:.2f}, Starve: {starvation_events}")
            
            results.append({
                "Scenario": scenario_name,
                "Model": agent_name,
                "Total Throughput": total_throughput,
                "Average Wait (s)": round(avg_w, 2),
                "Average Queue (veh)": round(avg_q, 2),
                "Starvation Events": starvation_events
            })
            
    out_csv = os.path.join(base_dir, "outputs", "evaluation_comparison_matrix.csv")
    with open(out_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Scenario", "Model", "Total Throughput", "Average Wait (s)", "Average Queue (veh)", "Starvation Events"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
            
    print(f"\nEvaluation summary saved to {out_csv}")

if __name__ == "__main__":
    evaluate_agent()
