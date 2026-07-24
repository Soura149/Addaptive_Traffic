import os
import sys
import csv
import glob
from pathlib import Path

# Add src to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from q_learning_agent import QLearningAgent
from generate_scenarios import generate_route_file
import traci

def run_extraction():
    base_dir = Path(r"C:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic")
    os.chdir(base_dir)
    
    data_dir = base_dir / "collected_data"
    output_dir = data_dir / "agent_runs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Identify unique scenarios from baseline
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    unique_scenarios = set()
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        parts = filename.replace('.csv', '').split('_')
        
        cars = None
        for p in parts:
            if p.endswith('total'):
                cars = int(p.replace('total', ''))
                
        balance = "unbalanced" if "unbalanced" in parts else "balanced"
        
        if cars is not None:
            unique_scenarios.add((cars, balance))
            
    print(f"Identified {len(unique_scenarios)} unique historical scenarios.")
    
    agent = QLearningAgent()
    if os.path.exists("outputs/q_table.json"):
        import json
        with open("outputs/q_table.json", 'r') as f:
            agent.q_table = json.load(f)
    
    agent.epsilon = 0.0  # Frozen evaluation mode
    
    headers = [
        "Step",
        "Queue_West_East",
        "Queue_North_South",
        "Queue_SD",
        "Arrival_West_East",
        "Arrival_North_South",
        "Throughput_Step",
        "Avg_Waiting_Time_West_East",
        "Avg_Waiting_Time_North_South",
        "WE_Green_Duration",
        "NS_Green_Duration"
    ]
    
    for cars, balance in sorted(list(unique_scenarios)):
        route_scenario_name = f"dynamic_{cars}_{balance}"
        route_filename = f"{route_scenario_name}.rou.xml"
        route_path = base_dir / "sumofiles" / "routes" / route_filename
        
        if balance == "balanced":
            we = cars // 2
            ns = cars // 2
            agent_filename = f"metrics_agent_cars_{cars}total_1000s.csv"
        else:
            we = int(cars * 0.75)
            ns = int(cars * 0.25)
            agent_filename = f"metrics_agent_cars_{cars}total_1000s_unbalanced.csv"
            
        # Call generate_route_file properly
        generate_route_file(route_scenario_name, {"we": we, "ns": ns})
        
        out_filepath = output_dir / agent_filename
        
        sumo_cmd = ["sumo", "-n", "sumofiles/Traci.net.xml", "-r", str(route_path), "--no-warnings"]
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
        
        we_queue, ns_queue, t_queue, we_wait, ns_wait, t_wait = get_metrics()
        state = agent.get_state(we_queue, ns_queue, we_wait, ns_wait)
        
        with open(out_filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            while traci.simulation.getMinExpectedNumber() > 0:
                action = agent.choose_action(state)
                
                traci.trafficlight.setPhase("J2", current_phase)
                
                arrived = 0
                for _ in range(action):
                    traci.simulationStep()
                    arrived += traci.simulation.getArrivedNumber()
                    if traci.simulation.getMinExpectedNumber() == 0:
                        break
                        
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
                    
                we_queue, ns_queue, t_queue, we_wait, ns_wait, t_wait = get_metrics()
                next_state = agent.get_state(we_queue, ns_queue, we_wait, ns_wait)
                
                queue_sd = abs(we_queue - ns_queue) / 2.0
                
                avg_wait_we = we_wait / 2.0 
                avg_wait_ns = ns_wait / 2.0
                
                sim_time = int(traci.simulation.getTime())
                
                writer.writerow([
                    sim_time,
                    we_queue,
                    ns_queue,
                    f"{queue_sd:.2f}",
                    0, 0, arrived,
                    f"{avg_wait_we:.2f}",
                    f"{avg_wait_ns:.2f}",
                    action if current_phase == 0 else 0,
                    action if current_phase == 2 else 0
                ])
                
                state = next_state
                
                # Yellow phase
                traci.trafficlight.setPhase("J2", current_phase + 1)
                for _ in range(3):
                    traci.simulationStep()
                    if traci.simulation.getMinExpectedNumber() == 0:
                        break
                        
                current_phase = 2 if current_phase == 0 else 0
                
        traci.close()
        
        with open(out_filepath, "r") as f:
            row_count = sum(1 for _ in f) - 1
            
        print(f"Generated {agent_filename} (Rows: {row_count})")
        
if __name__ == '__main__':
    run_extraction()
