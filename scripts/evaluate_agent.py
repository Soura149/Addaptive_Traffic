import os
import sys
import json
import csv

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_DIR, "src"))

from q_learning_agent import QLearningAgent
import traci
from sumolib import checkBinary

SCENARIOS = [
    "s1_low_200.rou.xml",
    "s2_medium_600.rou.xml",
    "s3_heavy_asym_1200.rou.xml",
    "s4_heavy_sym_1200.rou.xml",
    "s5_peak_1800.rou.xml"
]

def run_evaluation_episode(agent, scenario_name, fixed_action=None):
    route_path = os.path.join(WORKSPACE_DIR, "sumofiles", "routes", scenario_name)
    net_path = os.path.join(WORKSPACE_DIR, "sumofiles", "Traci.net.xml")
    
    cmd = [checkBinary('sumo'), "-n", net_path, "-r", route_path, "--no-step-log", "true", "--no-warnings", "true", "--time-to-teleport", "-1"]
    traci.start(cmd)
    
    we_edges = ["E0"]
    ns_edges = ["E1"]
    
    def get_metrics():
        we_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in we_edges)
        ns_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in ns_edges)
        we_w = sum(traci.edge.getWaitingTime(e) for e in we_edges)
        ns_w = sum(traci.edge.getWaitingTime(e) for e in ns_edges)
        return we_q, ns_q, we_q + ns_q, we_w, ns_w, we_w + ns_w

    sum_q = 0
    sum_w = 0
    total_throughput = 0
    decisions = 0
    starvation_events = 0
    
    current_phase = 0
    we_q, ns_q, t_q, we_w, ns_w, t_w = get_metrics()
    
    while traci.simulation.getMinExpectedNumber() > 0:
        if fixed_action is not None:
            action = fixed_action
        else:
            state = agent.get_state(we_q, ns_q, we_w, ns_w)
            action = agent.choose_action(state)
            
        traci.trafficlight.setPhase("J2", current_phase)
        
        arrived = 0
        for _ in range(action):
            traci.simulationStep()
            arrived += traci.simulation.getArrivedNumber()
            if traci.simulation.getMinExpectedNumber() == 0:
                break
                
        total_throughput += arrived
        
        next_we_q, next_ns_q, next_t_q, next_we_w, next_ns_w, next_t_w = get_metrics()
        
        if next_we_w > 100.0 or next_ns_w > 100.0:
            starvation_events += 1
            
        sum_q += next_t_q
        sum_w += next_t_w
        decisions += 1
        
        we_q, ns_q, t_q, we_w, ns_w, t_w = next_we_q, next_ns_q, next_t_q, next_we_w, next_ns_w, next_t_w
        
        if traci.simulation.getMinExpectedNumber() == 0:
            break
            
        traci.trafficlight.setPhase("J2", current_phase + 1)
        for _ in range(3):
            traci.simulationStep()
            if traci.simulation.getMinExpectedNumber() == 0:
                break
                
        current_phase = 2 if current_phase == 0 else 0
        
    traci.close()
    
    avg_q = sum_q / decisions if decisions > 0 else 0
    avg_w = sum_w / decisions if decisions > 0 else 0
    
    return total_throughput, avg_w, avg_q, starvation_events

def main():
    print("Starting Frozen Evaluation (epsilon=0, alpha=0)...")
    
    agent = QLearningAgent(alpha=0.0, epsilon=0.0)
    q_table_path = os.path.join(WORKSPACE_DIR, "outputs", "q_table.json")
    
    if os.path.exists(q_table_path):
        with open(q_table_path, 'r') as f:
            agent.q_table = json.load(f)
        print("Loaded Frozen Q-Table successfully.")
    else:
        print("CRITICAL: outputs/q_table.json not found!")
        sys.exit(1)
        
    policies = ["RL_Agent", "Fixed_10s", "Fixed_20s", "Fixed_30s", "Fixed_45s"]
    results = {sc: {} for sc in SCENARIOS}
    
    for scenario in SCENARIOS:
        print(f"\nEvaluating Scenario: {scenario}")
        
        for policy in policies:
            print(f"  -> Running {policy}...")
            fixed_val = None
            if policy.startswith("Fixed_"):
                fixed_val = int(policy.split("_")[1].replace("s", ""))
                
            T, avg_w, avg_q, starvations = run_evaluation_episode(agent, scenario, fixed_val)
            
            results[scenario][policy] = {
                "Throughput": T,
                "AvgWait": avg_w,
                "AvgQueue": avg_q,
                "Starvations": starvations
            }

    out_csv = os.path.join(WORKSPACE_DIR, "outputs", "evaluation_comparison_matrix.csv")
    with open(out_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Scenario", "Policy", "Throughput", "AvgWait", "AvgQueue", "Starvations"])
        for sc in SCENARIOS:
            for pol in policies:
                r = results[sc][pol]
                writer.writerow([sc, pol, r["Throughput"], round(r["AvgWait"], 2), round(r["AvgQueue"], 2), r["Starvations"]])

    print("\n" + "="*80)
    print("STEP 5: EVALUATION COMPARISON MATRIX".center(80))
    print("="*80)
    
    for sc in SCENARIOS:
        print(f"\nSCENARIO: {sc}")
        print(f"{'Policy':<15} | {'Throughput':<10} | {'Avg Wait(s)':<12} | {'Avg Queue':<10} | {'Starvations'}")
        print("-" * 70)
        for pol in policies:
            r = results[sc][pol]
            starv_flag = f"{r['Starvations']} (!)" if r['Starvations'] > 0 else str(r['Starvations'])
            print(f"{pol:<15} | {r['Throughput']:<10} | {r['AvgWait']:<12.2f} | {r['AvgQueue']:<10.2f} | {starv_flag}")
            
    print("\nSaved comprehensive results to outputs/evaluation_comparison_matrix.csv")

if __name__ == "__main__":
    main()
