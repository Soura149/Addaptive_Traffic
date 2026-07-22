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

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "..")

SCENARIOS = [
    "s1_low_200.rou.xml",
    "s2_medium_600.rou.xml",
    "s3_heavy_asym_1200.rou.xml",
    "s4_heavy_sym_1200.rou.xml",
    "s5_peak_1800.rou.xml"
]

ACTIONS = [10, 20, 30, 45, "random"]

def run_simulation(route_file, action_policy):
    net_file = os.path.join(WORKSPACE_DIR, "sumofiles", "Traci.net.xml")
    route_path = os.path.join(WORKSPACE_DIR, "sumofiles", "routes", route_file)
    sumo_cmd = [
        checkBinary('sumo'), 
        "-n", net_file, 
        "-r", route_path, 
        "--no-step-log", "true", 
        "--no-warnings", "true",
        "--time-to-teleport", "-1" # Prevent teleports if possible, or leave default
    ]
    
    traci.start(sumo_cmd)
    
    W_min, W_max = float('inf'), 0
    Q_min, Q_max = float('inf'), 0
    T_min, T_max = float('inf'), 0
    
    edges = ["E0", "E1"]
    current_phase = 0 # 0: WE Green, 2: NS Green
    
    while traci.simulation.getMinExpectedNumber() > 0:
        if action_policy == "random":
            duration = random.choice([10, 20, 30, 45])
        else:
            duration = action_policy
            
        traci.trafficlight.setPhase("J2", current_phase)
        
        arrived = 0
        for _ in range(duration):
            traci.simulationStep()
            arrived += traci.simulation.getArrivedNumber()
            if traci.simulation.getMinExpectedNumber() == 0:
                break
                
        # Record state at the end of green phase
        q = sum(traci.edge.getLastStepHaltingNumber(e) for e in edges)
        w = sum(traci.edge.getWaitingTime(e) for e in edges)
        t_rate = arrived / duration
        
        W_min = min(W_min, w)
        W_max = max(W_max, w)
        Q_min = min(Q_min, q)
        Q_max = max(Q_max, q)
        T_min = min(T_min, t_rate)
        T_max = max(T_max, t_rate)
        
        if traci.simulation.getMinExpectedNumber() == 0:
            break
            
        # Yellow phase
        traci.trafficlight.setPhase("J2", current_phase + 1)
        for _ in range(3):
            traci.simulationStep()
            if traci.simulation.getMinExpectedNumber() == 0:
                break
                
        current_phase = 2 if current_phase == 0 else 0
        
    traci.close()
    
    return W_min, W_max, Q_min, Q_max, T_min, T_max

def main():
    print("Starting Global Dynamic Calibration (Headless)...")
    
    global_W_min, global_W_max = float('inf'), 0
    global_Q_min, global_Q_max = float('inf'), 0
    global_T_min, global_T_max = float('inf'), 0
    
    scenario_bounds = {}
    
    for scenario in SCENARIOS:
        print(f"\nEvaluating Scenario: {scenario}")
        s_W_min, s_W_max = float('inf'), 0
        s_Q_min, s_Q_max = float('inf'), 0
        s_T_min, s_T_max = float('inf'), 0
        
        for action in ACTIONS:
            print(f"  -> Running Policy: {action}")
            W_min, W_max, Q_min, Q_max, T_min, T_max = run_simulation(scenario, action)
            
            s_W_min = min(s_W_min, W_min)
            s_W_max = max(s_W_max, W_max)
            s_Q_min = min(s_Q_min, Q_min)
            s_Q_max = max(s_Q_max, Q_max)
            s_T_min = min(s_T_min, T_min)
            s_T_max = max(s_T_max, T_max)
            
        scenario_bounds[scenario] = {
            "W_min": round(s_W_min, 2), "W_max": round(s_W_max, 2),
            "Q_min": round(s_Q_min, 2), "Q_max": round(s_Q_max, 2),
            "T_min": round(s_T_min, 4), "T_max": round(s_T_max, 4)
        }
        
        print(f"  [Bounds] W: {s_W_min:.1f}-{s_W_max:.1f}, Q: {s_Q_min}-{s_Q_max}, T: {s_T_min:.3f}-{s_T_max:.3f}")
        
        global_W_min = min(global_W_min, s_W_min)
        global_W_max = max(global_W_max, s_W_max)
        global_Q_min = min(global_Q_min, s_Q_min)
        global_Q_max = max(global_Q_max, s_Q_max)
        global_T_min = min(global_T_min, s_T_min)
        global_T_max = max(global_T_max, s_T_max)

    # Safegaurds: if max == min, slightly inflate max to avoid zero-denominator during normalization later.
    if global_W_max == global_W_min: global_W_max += 1.0
    if global_Q_max == global_Q_min: global_Q_max += 1.0
    if global_T_max == global_T_min: global_T_max += 0.1

    final_bounds = {
        "W_min": round(global_W_min, 2),
        "W_max": round(global_W_max, 2),
        "Q_min": round(global_Q_min, 2),
        "Q_max": round(global_Q_max, 2),
        "T_min": round(global_T_min, 4),
        "T_max": round(global_T_max, 4)
    }
    
    out_dir = os.path.join(WORKSPACE_DIR, "src")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "calibration_bounds.json")
    
    with open(out_path, "w") as f:
        json.dump(final_bounds, f, indent=4)
        
    print("\n=========================================================================")
    print("                     STEP 2: CALIBRATION SUMMARY TABLE                   ")
    print("=========================================================================")
    print(f"{'Scenario':<25} | {'W (sec)':<15} | {'Q (veh)':<12} | {'T (veh/s)'}")
    print("-" * 73)
    for sc, b in scenario_bounds.items():
        w_str = f"{b['W_min']}-{b['W_max']}"
        q_str = f"{b['Q_min']}-{b['Q_max']}"
        t_str = f"{b['T_min']:.2f}-{b['T_max']:.2f}"
        print(f"{sc:<25} | {w_str:<15} | {q_str:<12} | {t_str}")
    print("=========================================================================")
    print("                          GLOBAL EXTREMA (SAVED)                         ")
    print("=========================================================================")
    print(f"Waiting Time W:  {final_bounds['W_min']} to {final_bounds['W_max']} seconds")
    print(f"Queue Length Q:  {final_bounds['Q_min']} to {final_bounds['Q_max']} vehicles")
    print(f"Throughput T:    {final_bounds['T_min']} to {final_bounds['T_max']} veh/s")
    print(f"-> Saved to {out_path}")
    print("=========================================================================")
    print("STATUS: 100% READINESS FOR STEP 3 (Agent Refactoring).")

if __name__ == "__main__":
    main()
