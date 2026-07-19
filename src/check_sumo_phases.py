import os
import sys
import time

# System environment initialization
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("CRITICAL ERROR: Please declare environment variable 'SUMO_HOME'")

import traci

def run_diagnostic():
    sumo_cfg = "src/Traci.sumocfg"
    sumo_binary = os.environ.get("SUMO_BINARY", "sumo") # Run headlessly for a quick check
    
    print("Starting standalone TraCI phase diagnostic...")
    traci.start([sumo_binary, "-c", sumo_cfg, "--start", "--quit-on-end"])
    
    # Automatically grab the traffic light junction ID
    tl_ids = traci.trafficlight.getIDList()
    if not tl_ids:
        print("ERROR: No traffic lights found in the network file!")
        traci.close()
        return
    
    junction_id = tl_ids[0]
    print(f"Found Active Traffic Light Junction ID: '{junction_id}'")
    
    print("\nExecuting test steps and forcing phase changes...")
    print(f"{'Simulation Step':<18} | {'Active Phase Index Read from SUMO'}")
    print("-" * 55)
    
    for step in range(1, 101):
        traci.simulationStep()
        
        # Test 1: Let it run naturally for the first 20 steps
        # Test 2: Manually cycle through phases 0, 1, 2, 3 to see if TraCI registers them
        if step == 25:
            traci.trafficlight.setPhase(junction_id, 1)
        elif step == 50:
            traci.trafficlight.setPhase(junction_id, 2)
        elif step == 75:
            traci.trafficlight.setPhase(junction_id, 3)
            
        current_phase = traci.trafficlight.getPhase(junction_id)
        
        # Log every 10 steps, or exactly when we force a change
        if step % 10 == 0 or step in [25, 26, 50, 51, 75, 76]:
            print(f"Step {step:<13} | Phase Index: {current_phase}")
            
    traci.close()
    print("\nDiagnostic complete.")

if __name__ == "__main__":
    run_diagnostic()
