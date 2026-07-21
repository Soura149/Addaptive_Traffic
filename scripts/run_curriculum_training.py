import os
import sys
import json
import csv
from pathlib import Path

# Add src to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from q_learning_agent import QLearningAgent
import traci

def main():
    base_dir = Path(r"C:\VSCODE\CISInternship_Implement")
    os.chdir(base_dir)

    # Clean existing logs
    files_to_clean = ["outputs/decision_log.csv", "outputs/training_episode_summary.csv", "src/q_table.json"]
    for f in files_to_clean:
        if os.path.exists(f):
            os.remove(f)
            
    os.makedirs("outputs", exist_ok=True)
    
    agent = QLearningAgent()
    
    curriculum = [
        ("sumofiles/routes/s1_low_200.rou.xml", 1, 20),
        ("sumofiles/routes/s2_medium_600.rou.xml", 21, 40),
        ("sumofiles/routes/s3_heavy_asym_1200.rou.xml", 41, 60),
        ("sumofiles/routes/s4_heavy_sym_1200.rou.xml", 61, 80),
        ("sumofiles/routes/s5_peak_1800.rou.xml", 81, 100)
    ]
    
    decision_log_path = "outputs/decision_log.csv"
    episode_log_path = "outputs/training_episode_summary.csv"
    
    with open(decision_log_path, "w", newline='') as d_file, open(episode_log_path, "w", newline='') as e_file:
        d_writer = csv.writer(d_file)
        d_writer.writerow(["Episode", "Decision", "State", "Action", "Next_State", "WE_Wait", "NS_Wait", "WE_Queue", "NS_Queue", "Total_Wait", "Total_Queue", "Throughput_Rate", "W_q", "T_q", "Q_q", "Reward", "Q_before", "Q_after"])
        
        e_writer = csv.writer(e_file)
        e_writer.writerow(["Episode", "Scenario", "Avg_Reward", "Avg_Wait", "Avg_Queue", "Throughput", "Epsilon", "Steps"])
        
        decision = 0
        
        print("="*80)
        print("STEP 4: MULTI-SCENARIO CURRICULUM TRAINING (100 EPISODES)")
        print("="*80)
        
        for scenario, start_ep, end_ep in curriculum:
            for ep in range(start_ep, end_ep + 1):
                sumo_cmd = ["sumo", "-n", "sumofiles/Traci.net.xml", "-r", scenario, "--no-warnings"]
                traci.start(sumo_cmd)
                
                ep_reward = 0
                ep_steps = 0
                total_wait_acc = 0
                total_queue_acc = 0
                total_arrived = 0
                ep_decisions = 0
                
                we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
                state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
                
                while traci.simulation.getMinExpectedNumber() > 0:
                    action_idx = agent.get_action(state, evaluate=False)
                    q_before = agent.q_table[state][action_idx]
                    
                    arrived, steps = agent.run_cycle(action_idx)
                    ep_steps += steps
                    total_arrived += arrived
                    
                    if traci.simulation.getMinExpectedNumber() == 0:
                        break
                        
                    we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
                    next_state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
                    
                    total_wait_acc += total_wait
                    total_queue_acc += total_queue
                    ep_decisions += 1
                    
                    T = arrived / steps if steps > 0 else 0
                    
                    W_q = agent._normalize(total_wait, agent.bounds["W_min"], agent.bounds["W_max"], invert=True)
                    Q_q = agent._normalize(total_queue, agent.bounds["Q_min"], agent.bounds["Q_max"], invert=True)
                    T_q = agent._normalize(T, agent.bounds["T_min"], agent.bounds["T_max"], invert=False)
                    P_s = 2.0 if (we_max_wait > 100.0 or ns_max_wait > 100.0) else 0.0
                    
                    reward = 0.50 * W_q + 0.30 * T_q + 0.20 * Q_q - P_s
                    
                    if next_state not in agent.q_table:
                        agent.q_table[next_state] = [0.0] * 9
                        
                    agent.q_table[state][action_idx] = q_before + agent.alpha * (reward + agent.gamma * max(agent.q_table[next_state]) - q_before)
                    q_after = agent.q_table[state][action_idx]
                    
                    ep_reward += reward
                    
                    d_writer.writerow([ep, decision, state, agent.actions[action_idx], next_state, f"{we_max_wait:.2f}", f"{ns_max_wait:.2f}", we_queue, ns_queue, f"{total_wait:.2f}", total_queue, f"{T:.4f}", f"{W_q:.4f}", f"{T_q:.4f}", f"{Q_q:.4f}", f"{reward:.4f}", f"{q_before:.4f}", f"{q_after:.4f}"])
                    decision += 1
                    state = next_state
                    
                traci.close()
                d_file.flush()
                
                avg_reward = ep_reward / ep_decisions if ep_decisions > 0 else 0
                avg_wait = total_wait_acc / ep_decisions if ep_decisions > 0 else 0
                avg_queue = total_queue_acc / ep_decisions if ep_decisions > 0 else 0
                throughput = total_arrived / ep_steps if ep_steps > 0 else 0
                
                e_writer.writerow([ep, os.path.basename(scenario), f"{avg_reward:.4f}", f"{avg_wait:.2f}", f"{avg_queue:.2f}", f"{throughput:.4f}", f"{agent.epsilon:.4f}", ep_steps])
                e_file.flush()
                
                print(f"Ep {ep:<3} [{os.path.basename(scenario):<25}] | AvgRwd: {avg_reward:>7.4f} | AvgWait: {avg_wait:>6.2f} | AvgQ: {avg_queue:>5.2f} | T-put: {throughput:>6.4f} | Eps: {agent.epsilon:.4f}")
                
                agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)
                agent.save_q_table("src/q_table.json")
                
    visited_states = len(agent.q_table)
    visited_actions = sum(1 for acts in agent.q_table.values() for a in acts if a != 0.0)
    
    print("\n" + "="*80)
    print("TRAINING COMPLETION SUMMARY")
    print("="*80)
    print(f"Total Episodes Run: 100")
    print(f"Total Unique States Visited: {visited_states}")
    print(f"Total State-Action Pairs Explored: {visited_actions}")
    print(f"Final Epsilon Value: {agent.epsilon:.4f}")
    
    print("\n" + "="*120)
    print("FINAL Q-TABLE (STATE -> ACTIONS)")
    print("Actions: 0:(10,10) 1:(20,10) 2:(30,10) 3:(45,15) 4:(10,20) 5:(10,30) 6:(20,20) 7:(30,30) 8:(45,45)")
    print("="*120)
    for s, acts in agent.q_table.items():
        row = f"| {s:<25} | " + " | ".join(f"{a:>7.4f}" for a in acts) + " |"
        print(row)
        
    print("STATUS: TRAINING COMPLETE")

if __name__ == '__main__':
    main()
