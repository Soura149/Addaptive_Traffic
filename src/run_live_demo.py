import os
import sys
import json
import time
import csv

# Ensure SUMO_HOME is declared in system paths
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("CRITICAL ERROR: Please declare environment variable 'SUMO_HOME'")

import traci

# Import the actual generator to avoid subprocess arguments mismatch
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from route_generator import generate_routes
except ImportError:
    pass # Will handle gracefully if missing

def generate_live_traffic(total_cars=1200):
    """
    Invokes the internal route generator to completely overwrite the heavy 
    XML routing matrix programmatically. No manual file editing needed.
    """
    print(f"[{time.strftime('%H:%M:%S')}] 🔄 Generating clean {total_cars}-car asymmetric traffic demand matrix...")
    we_count = int(total_cars * 0.75)
    ns_count = int(total_cars * 0.25)
    
    route_file = "src/Traci.rou.xml" if os.path.exists("src/Traci.rou.xml") else "sumofiles/Traci.rou.xml"
    try:
        generate_routes(route_file, episode_seed=total_cars, we_count=we_count, ns_count=ns_count)
        print(f"[{time.strftime('%H:%M:%S')}] 🛣️ Route configuration file successfully compiled.")
    except Exception as e:
        print(f"[!] Warning during programmatic route generation: {e}")
        print("Continuing with existing route configuration file...")

def load_q_table(q_table_path):
    print(f"[{time.strftime('%H:%M:%S')}] 🧠 Loading trained AI matrix from: {q_table_path}")
    with open(q_table_path, 'r') as f:
        return json.load(f)

def get_state(we_max_wait, ns_max_wait, we_queue, ns_queue):
    """
    Matches the exact state formulation used in q_learning_agent.py
    """
    def categorize_queue(q):
        if q < 3: return "Low"
        elif q <= 5: return "Medium"
        else: return "High"
        
    we_q = categorize_queue(we_queue)
    ns_q = categorize_queue(ns_queue)
    starving = "Starving" if (we_max_wait > 100.0 or ns_max_wait > 100.0) else "NoStarvation"
    return f"{we_q}*{ns_q}*{starving}"

def run_live_demonstration(num_vehicles=1200):
    # Set proper environment infrastructure paths
    sumo_cfg = "src/Traci.sumocfg"
    q_table_file = "src/q_table.json"
    
    if not os.path.exists(sumo_cfg):
        sumo_cfg = "sumofiles/Traci.sumocfg"

    # Step 1: Automate the creation of the heavy XML vehicle routing schedule
    generate_live_traffic(total_cars=num_vehicles)

    # Step 2: Extract the frozen brain parameters
    q_table = load_q_table(q_table_file)
    
    # Step 3: Spin up the SUMO graphics engine
    sumo_binary = os.environ.get("SUMO_BINARY", "sumo-gui")
    print(f"[{time.strftime('%H:%M:%S')}] 🚦 Initializing TraCI API & Triggering SUMO Network Engine...")
    
    # Removed --start and --quit-on-end so you can manually play/pause in the GUI
    traci.start([sumo_binary, "-c", sumo_cfg])
    
    ACTIONS = [(10, 10), (20, 10), (30, 10), (45, 15), (10, 20), (10, 30), (20, 20), (30, 30), (45, 45)]
    
    os.makedirs("collected_data/agent_runs", exist_ok=True)
    csv_file = open("collected_data/agent_runs/live_demo_metrics.csv", "w", newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        "decision_step", "sim_time", "state", "chosen_action_id", 
        "we_green_time", "ns_green_time", "active_phase", 
        "we_queue_length", "ns_queue_length", 
        "we_max_wait", "ns_max_wait", "total_waiting_time"
    ])
    
    
    print("\n" + "="*85)
    print("        LIVE AGENT REAL-TIME SIGNAL TIMING & PERFORMANCE TERMINAL DASHBOARD       ")
    print("="*85)
    print(f"{'Step':<6} | {'Sim Time':<9} | {'State':<10} | {'Selected Signal Timing':<22} | {'WE Cars':<8} | {'NS Cars':<8} | {'Wait Time':<9}")
    print("-"*85)

    step = 0
    
    try:
        last_logged_state = None
        
        while traci.simulation.getMinExpectedNumber() > 0:
            # Correct edge IDs: E0 for West-East, E1 for North-South
            we_queue = int(traci.edge.getLastStepHaltingNumber("E0")) 
            ns_queue = int(traci.edge.getLastStepHaltingNumber("E1"))
            
            we_vehs = traci.edge.getLastStepVehicleIDs("E0")
            ns_vehs = traci.edge.getLastStepVehicleIDs("E1")
            
            we_max_wait = max([traci.vehicle.getWaitingTime(v) for v in we_vehs]) if we_vehs else 0.0
            ns_max_wait = max([traci.vehicle.getWaitingTime(v) for v in ns_vehs]) if ns_vehs else 0.0
            total_waiting_time = sum(traci.vehicle.getWaitingTime(v) for v in we_vehs) + sum(traci.vehicle.getWaitingTime(v) for v in ns_vehs)
            
            # Map raw vehicle numbers to the exact state key space from training
            current_state = get_state(we_max_wait, ns_max_wait, we_queue, ns_queue)
            
            sim_time = traci.simulation.getTime()
            
            # Pure exploitation policy lookup (Epsilon = 0.0)
            if current_state in q_table:
                q_values = q_table[current_state]
                chosen_action = q_values.index(max(q_values))
                we_dur, ns_dur = ACTIONS[chosen_action]
                timing_display = f"{we_dur}s WE / {ns_dur}s NS"
            else:
                chosen_action = 0  
                we_dur, ns_dur = ACTIONS[0]
                timing_display = "10s WE / 10s NS (Unseen State - Default)"

            if current_state != last_logged_state or step % 20 == 0:
                print(f"{step:<6} | {sim_time:<8.1f}s | {current_state:<10} | {timing_display:<22} | {we_queue:<8} | {ns_queue:<8} | {total_waiting_time:<8.1f}s")
                last_logged_state = current_state
            
            # WE Green
            traci.trafficlight.setPhase("J2", 0)
            for _ in range(we_dur):
                traci.simulationStep()
                if traci.simulation.getMinExpectedNumber() == 0: break
                
            csv_writer.writerow([
                step, int(traci.simulation.getTime()), current_state, chosen_action,
                we_dur, ns_dur, "WE_GREEN", 
                we_queue, ns_queue, we_max_wait, ns_max_wait, total_waiting_time
            ])
            
            if traci.simulation.getMinExpectedNumber() == 0: break
            
            # WE Yellow
            traci.trafficlight.setPhase("J2", 1)
            for _ in range(3):
                traci.simulationStep()
                if traci.simulation.getMinExpectedNumber() == 0: break
                
            if traci.simulation.getMinExpectedNumber() == 0: break
            
            # NS Green
            traci.trafficlight.setPhase("J2", 2)
            for _ in range(ns_dur):
                traci.simulationStep()
                if traci.simulation.getMinExpectedNumber() == 0: break
                
            csv_writer.writerow([
                step, int(traci.simulation.getTime()), current_state, chosen_action,
                we_dur, ns_dur, "NS_GREEN", 
                we_queue, ns_queue, we_max_wait, ns_max_wait, total_waiting_time
            ])
            
            if traci.simulation.getMinExpectedNumber() == 0: break
            
            # NS Yellow
            traci.trafficlight.setPhase("J2", 3)
            for _ in range(3):
                traci.simulationStep()
                if traci.simulation.getMinExpectedNumber() == 0: break
                
            step += 1
            
    except traci.exceptions.FatalTraCIError:
        print("\n[!] SUMO user interface window closed by viewer.")
    finally:
        csv_file.close()
        try:
            traci.close()
        except:
            pass
        print("\n" + "="*70)
        print(" 🎉 Live Demonstration Evaluation Phase Successfully Concluded!")
        print("="*70)

if __name__ == "__main__":
    # If your sir wants to change the vehicle scenario on the fly, 
    # simply adjust this integer parameter right here.
    run_live_demonstration(num_vehicles=1200)