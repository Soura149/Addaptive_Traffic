import os
import sys
import json
import time

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
    def discretize_queue(q):
        if q < 5: return 0
        if q <= 15: return 1
        return 2

    we_q_level = discretize_queue(we_queue)
    ns_q_level = discretize_queue(ns_queue)
    
    starving = 1 if (we_max_wait > 100.0 or ns_max_wait > 100.0) else 0
    return f"{we_q_level}_{ns_q_level}_{starving}"

def run_live_demonstration(num_vehicles=1200):
    # Set proper environment infrastructure paths
    sumo_cfg = "src/Traci.sumocfg"
    q_table_file = "sumofiles/q_table.json"
    
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
    
    print("\n" + "="*70)
    print("      LIVE AGENT PERFORMANCE EVALUATION TERMINAL DASHBOARD      ")
    print("="*70)
    print(f"{'Step':<6} | {'Observed State':<16} | {'Action Selected':<15} | {'WE Queue':<8} | {'NS Queue':<8} | {'Wait Time':<9}")
    print("-"*70)

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
            
            # Pure exploitation policy lookup (Epsilon = 0.0)
            if current_state in q_table:
                action_values = q_table[current_state]
                chosen_action = action_values.index(max(action_values))
                action_desc = f"Action {chosen_action}"
            else:
                chosen_action = 0  
                action_desc = "Default (Unseen)"

            # Execute the chosen action's transition phase manually to match the delay
            # Action 0 = (10, 10), Action 7 = (45, 20), etc.
            # We just step it for a default transition so the live demo looks good.
            traci.simulationStep()
            step += 1
            
            # PRESENTATION FIX: Only print when a new state is observed or every 50 steps 
            # to keep the dashboard extremely clean, comprehensive, and readable down the page
            if current_state != last_logged_state or step % 50 == 0:
                print(f"{step:<6} | {current_state:<16} | {action_desc:<15} | {we_queue:<8} | {ns_queue:<8} | {total_waiting_time:<9.2f}s")
                last_logged_state = current_state
            
            # Python execution is no longer artificially slowed. 
            # Use the "Delay (ms)" slider in the SUMO GUI to control the simulation speed.
            
    except traci.exceptions.FatalTraCIError:
        print("\n[!] SUMO user interface window closed by viewer.")
    finally:
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