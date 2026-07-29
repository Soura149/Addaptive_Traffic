import os
import sys
import json
import random

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

import traci
from sumolib import checkBinary

def run_calibration():
    base_dir = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"
    routes_dir = os.path.join(base_dir, "sumofiles", "routes")
    net_file = os.path.join(base_dir, "sumofiles", "Traci.net.xml")
    
    vols = [100, 300, 600, 900, 1200]
    timings = [10, 20, 30, 45]
    
    # Initialize global min/max
    W_min, W_max = float('inf'), float('-inf')
    Q_min, Q_max = float('inf'), float('-inf')
    T_min, T_max = float('inf'), float('-inf')
    
    sumoBinary = checkBinary('sumo')
    
    print("Starting Step 2 Global Calibration...")
    
    for we_vol in vols:
        for ns_vol in vols:
            route_file = os.path.join(routes_dir, f"route_we_{we_vol}_ns_{ns_vol}.rou.xml")
            
            # Start SUMO headless
            cmd = [
                sumoBinary,
                "-n", net_file,
                "-r", route_file,
                "--no-step-log", "true",
                "--time-to-teleport", "-1",
                "--no-warnings", "true"
            ]
            traci.start(cmd)
            
            step = 0
            while traci.simulation.getMinExpectedNumber() > 0:
                phase = random.choice([0, 2]) # 0 is WE Green, 2 is NS Green
                duration = random.choice(timings)
                
                current_phase = traci.trafficlight.getPhase("J2")
                
                # Yellow transition if switching phases
                if current_phase != phase and current_phase in [0, 2]:
                    yellow_phase = 1 if current_phase == 0 else 3
                    traci.trafficlight.setPhase("J2", yellow_phase)
                    for _ in range(3):
                        traci.simulationStep()
                        step += 1
                        if traci.simulation.getMinExpectedNumber() == 0:
                            break
                            
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
                    
                traci.trafficlight.setPhase("J2", phase)
                
                actual_duration = 0
                completed_vehicles = 0
                
                for _ in range(duration):
                    traci.simulationStep()
                    completed_vehicles += traci.simulation.getArrivedNumber()
                    step += 1
                    actual_duration += 1
                    if traci.simulation.getMinExpectedNumber() == 0:
                        break
                
                # Calculate metrics at the end of the action
                if actual_duration > 0:
                    T = completed_vehicles / actual_duration
                else:
                    T = 0
                
                W = traci.edge.getWaitingTime("E0") + traci.edge.getWaitingTime("E1")
                Q = traci.edge.getLastStepHaltingNumber("E0") + traci.edge.getLastStepHaltingNumber("E1")
                
                if W < W_min: W_min = W
                if W > W_max: W_max = W
                
                if Q < Q_min: Q_min = Q
                if Q > Q_max: Q_max = Q
                
                if T < T_min: T_min = T
                if T > T_max: T_max = T

            traci.close()
            
    # Safeguard & Zero-Denominator Protection
    if W_min == W_max: W_max = W_min + 1.0
    if Q_min == Q_max: Q_max = Q_min + 1.0
    if T_min == T_max: T_max = T_min + 1.0
    
    # Enforce human-tolerance caps on the dynamic bounds
    W_max = min(W_max, 150.0) # Cap wait time penalty scaling at 2.5 mins
    Q_max = max(Q_max, 30.0)  # Ensure queue penalty scaling isn't overly sensitive
    
    bounds = {
        "W_min": W_min,
        "W_max": W_max,
        "Q_min": Q_min,
        "Q_max": Q_max,
        "T_min": T_min,
        "T_max": T_max
    }
    
    out_file = os.path.join(base_dir, "src", "calibration_bounds.json")
    with open(out_file, 'w') as f:
        json.dump(bounds, f, indent=4)
        
    print("\n--- Global Extrema Summary ---")
    print(f"Waiting Time (W): Min = {W_min:.2f} s, Max = {W_max:.2f} s")
    print(f"Queue Length (Q): Min = {Q_min:.2f} veh, Max = {Q_max:.2f} veh")
    print(f"Throughput Rate (T): Min = {T_min:.4f} veh/s, Max = {T_max:.4f} veh/s")
    print(f"\nSaved calibration bounds to {out_file}")

if __name__ == "__main__":
    run_calibration()
