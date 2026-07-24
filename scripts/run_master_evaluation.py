import os
import sys
import json
import csv
from pathlib import Path

# Add src to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from q_learning_agent import QLearningAgent
import traci

def run_evaluation(agent, scenario, controller_type):
    sumo_cmd = ["sumo", "-n", "sumofiles/Traci.net.xml", "-r", scenario, "--no-warnings"]
    traci.start(sumo_cmd)
    
    total_wait_acc = 0
    total_queue_acc = 0
    total_arrived = 0
    ep_steps = 0
    ep_decisions = 0
    starvation_incidents = 0
    
    try:
        total_injected = int(os.path.basename(scenario).split('_')[-1].split('.')[0])
    except:
        total_injected = 1200
        
    while traci.simulation.getMinExpectedNumber() > 0:
        we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
        state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
        
        if controller_type == "Fixed-10s":
            action_idx = 0
        elif controller_type == "Fixed-20s":
            action_idx = 6
        elif controller_type == "Fixed-30s":
            action_idx = 7
        elif controller_type == "Fixed-45s":
            action_idx = 8
        elif controller_type == "Q-Agent":
            action_idx = agent.get_action(state, evaluate=True)
            
        arrived, steps = agent.run_cycle(action_idx)
        
        ep_steps += steps
        total_arrived += arrived
        
        if traci.simulation.getMinExpectedNumber() == 0:
            break
            
        we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
        
        total_wait_acc += total_wait
        total_queue_acc += total_queue
        ep_decisions += 1
        
        if we_max_wait > 100.0 or ns_max_wait > 100.0:
            starvation_incidents += 1
            
    traci.close()
    
    avg_wait = total_wait_acc / ep_decisions if ep_decisions > 0 else 0
    avg_queue = total_queue_acc / ep_decisions if ep_decisions > 0 else 0
    throughput = (total_arrived / total_injected) * 100 if total_injected > 0 else 100.0
    
    return throughput, avg_wait, avg_queue, starvation_incidents, ep_steps

def main():
    base_dir = Path(r"C:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic")
    os.chdir(base_dir)
    os.makedirs("outputs", exist_ok=True)
    
    agent = QLearningAgent()
    agent.epsilon = 0.0
    
    scenarios = [
        "sumofiles/routes/s1_low_200.rou.xml",
        "sumofiles/routes/s2_medium_600.rou.xml",
        "sumofiles/routes/s3_heavy_asym_1200.rou.xml",
        "sumofiles/routes/s4_heavy_sym_1200.rou.xml",
        "sumofiles/routes/s5_peak_1800.rou.xml"
    ]
    
    controllers = ["Fixed-10s", "Fixed-20s", "Fixed-30s", "Fixed-45s", "Q-Agent"]
    
    out_path = "outputs/performance_benchmark_matrix.csv"
    with open(out_path, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Scenario", "Controller", "Completion_Rate(%)", "Avg_Wait", "Avg_Queue", "Starvation_Incidents", "Simulation_Steps"])
        
        results = []
        
        for scenario in scenarios:
            scenario_name = os.path.basename(scenario)
            print(f"Evaluating Scenario: {scenario_name}")
            for c in controllers:
                throughput, avg_wait, avg_queue, starvation, steps = run_evaluation(agent, scenario, c)
                writer.writerow([scenario_name, c, f"{throughput:.1f}", f"{avg_wait:.2f}", f"{avg_queue:.2f}", starvation, steps])
                f.flush()
                results.append((scenario_name, c, throughput, avg_wait, avg_queue, starvation, steps))
                print(f"  [{c:10}] Wait: {avg_wait:6.2f}s | Queue: {avg_queue:5.2f} | Starves: {starvation:3} | Steps: {steps}")
                
    # Generate Markdown Summary
    print("\n" + "="*80)
    print("STEP 5 EVALUATION BENCHMARK REPORT")
    print("="*80)
    print("| Scenario | Controller | Avg Wait (s) | Avg Queue | Starves | Steps |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        print(f"| {r[0]} | **{r[1]}** | {r[3]:.2f} | {r[4]:.2f} | {r[5]} | {r[6]} |")
        
if __name__ == '__main__':
    main()
