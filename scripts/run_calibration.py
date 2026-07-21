import os
import sys
import json
import random
from pathlib import Path

# Ensure SUMO_HOME is declared in system paths
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("CRITICAL ERROR: Please declare environment variable 'SUMO_HOME'")

import traci

def run_transition(d_green, phase_green, phase_yellow, edges=["E0", "E1"]):
    traci.trafficlight.setPhase("J2", phase_green)
    
    arrived = 0
    steps_taken = 0
    
    # Green phase
    for _ in range(d_green):
        traci.simulationStep()
        arrived += traci.simulation.getArrivedNumber()
        steps_taken += 1
        if traci.simulation.getMinExpectedNumber() == 0: break
        
    # Yellow phase
    if traci.simulation.getMinExpectedNumber() > 0:
        traci.trafficlight.setPhase("J2", phase_yellow)
        for _ in range(3):
            traci.simulationStep()
            arrived += traci.simulation.getArrivedNumber()
            steps_taken += 1
            if traci.simulation.getMinExpectedNumber() == 0: break
            
    # Measure W, Q at the end of transition
    W = sum(traci.edge.getWaitingTime(e) for e in edges)
    Q = sum(traci.edge.getLastStepHaltingNumber(e) for e in edges)
    T = arrived / steps_taken if steps_taken > 0 else 0
    
    return W, Q, T

def run_simulation(scenario_file, policy):
    sumo_cmd = ["sumo", "-n", "sumofiles/Traci.net.xml", "-r", f"sumofiles/routes/{scenario_file}", "--no-warnings"]
    traci.start(sumo_cmd)
    
    records = []
    
    while traci.simulation.getMinExpectedNumber() > 0:
        if policy == 'random':
            d_we = random.choice([10, 20, 30, 45])
        else:
            d_we = policy
            
        w, q, t = run_transition(d_we, 0, 1)
        records.append((w, q, t))
        
        if traci.simulation.getMinExpectedNumber() == 0:
            break
            
        if policy == 'random':
            d_ns = random.choice([10, 20, 30, 45])
        else:
            d_ns = policy
            
        w, q, t = run_transition(d_ns, 2, 3)
        records.append((w, q, t))

    traci.close()
    return records

def main():
    base_dir = Path(r"C:\VSCODE\CISInternship_Implement")
    os.chdir(base_dir)
    
    scenarios = [
        "s1_low_200.rou.xml",
        "s2_medium_600.rou.xml",
        "s3_heavy_asym_1200.rou.xml",
        "s4_heavy_sym_1200.rou.xml",
        "s5_peak_1800.rou.xml"
    ]
    
    policies = [10, 20, 30, 45, 'random']
    
    global_min = {"W": float('inf'), "Q": float('inf'), "T": float('inf')}
    global_max = {"W": -float('inf'), "Q": -float('inf'), "T": -float('inf')}
    
    scenario_stats = {}
    
    print("="*80)
    print("STEP 2: DYNAMIC MIN-MAX CALIBRATION PHASE")
    print("="*80)
    
    for scenario in scenarios:
        print(f"Running Calibration for Scenario: {scenario}")
        s_min = {"W": float('inf'), "Q": float('inf'), "T": float('inf')}
        s_max = {"W": -float('inf'), "Q": -float('inf'), "T": -float('inf')}
        
        for policy in policies:
            records = run_simulation(scenario, policy)
            
            for w, q, t in records:
                s_min["W"] = min(s_min["W"], w)
                s_max["W"] = max(s_max["W"], w)
                s_min["Q"] = min(s_min["Q"], q)
                s_max["Q"] = max(s_max["Q"], q)
                s_min["T"] = min(s_min["T"], t)
                s_max["T"] = max(s_max["T"], t)
                
                global_min["W"] = min(global_min["W"], w)
                global_max["W"] = max(global_max["W"], w)
                global_min["Q"] = min(global_min["Q"], q)
                global_max["Q"] = max(global_max["Q"], q)
                global_min["T"] = min(global_min["T"], t)
                global_max["T"] = max(global_max["T"], t)
                
        scenario_stats[scenario] = {"min": s_min, "max": s_max}
        
    print("\n" + "="*80)
    print("PER-SCENARIO CALIBRATION BOUNDS")
    print("="*80)
    print(f"{'Scenario':<30} | {'W_min':<8} | {'W_max':<8} | {'Q_min':<8} | {'Q_max':<8} | {'T_min':<8} | {'T_max':<8}")
    print("-" * 80)
    for scenario, stat in scenario_stats.items():
        smin, smax = stat["min"], stat["max"]
        print(f"{scenario:<30} | {smin['W']:<8.2f} | {smax['W']:<8.2f} | {smin['Q']:<8.2f} | {smax['Q']:<8.2f} | {smin['T']:<8.2f} | {smax['T']:<8.2f}")
        
    print("\n" + "="*80)
    print("GLOBAL CALIBRATION BOUNDS")
    print("="*80)
    print(f"W_min: {global_min['W']:.2f}, W_max: {global_max['W']:.2f}")
    print(f"Q_min: {global_min['Q']:.2f}, Q_max: {global_max['Q']:.2f}")
    print(f"T_min: {global_min['T']:.2f}, T_max: {global_max['T']:.2f}")
    
    # Mathematical validity check / Zero-Denominator Protection
    if global_min["W"] == global_max["W"]: global_max["W"] += 1.0
    if global_min["Q"] == global_max["Q"]: global_max["Q"] += 1.0
    if global_min["T"] == global_max["T"]: global_max["T"] += 1.0
    
    # Save to json
    bounds = {
        "W_min": global_min["W"], "W_max": global_max["W"],
        "Q_min": global_min["Q"], "Q_max": global_max["Q"],
        "T_min": global_min["T"], "T_max": global_max["T"]
    }
    
    os.makedirs("src", exist_ok=True)
    with open("src/calibration_bounds.json", "w") as f:
        json.dump(bounds, f, indent=4)
        
    print("\nSTATUS: CALIBRATION COMPLETE")
    print("Global bounds successfully saved to src/calibration_bounds.json")

if __name__ == '__main__':
    main()
