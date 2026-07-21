import os
import sys
import json
import random
import csv
import argparse
from pathlib import Path

# Add SUMO tools
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("CRITICAL ERROR: Please declare environment variable 'SUMO_HOME'")

import traci

class QLearningAgent:
    def __init__(self):
        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 1.0
        self.epsilon_decay = 0.95
        self.epsilon_min = 0.01
        
        self.actions = [(10, 10), (20, 10), (30, 10), (45, 15), (10, 20), (10, 30), (20, 20), (30, 30), (45, 45)]
        self.q_table = {}
        
        with open("src/calibration_bounds.json", "r") as f:
            self.bounds = json.load(f)
            
    def load_q_table(self, path):
        if os.path.exists(path):
            with open(path, "r") as f:
                self.q_table = json.load(f)
                
    def save_q_table(self, path):
        with open(path, "w") as f:
            json.dump(self.q_table, f, indent=4)

    def _normalize(self, val, v_min, v_max, invert=False):
        if v_max == v_min:
            return 0.5
        norm = (val - v_min) / (v_max - v_min)
        # Ensure bounds clamping just in case empirical bounds are exceeded slightly
        norm = max(0.0, min(1.0, norm))
        if invert:
            return 1.0 - norm
        return norm

    def get_state(self, we_queue, ns_queue, we_max_wait, ns_max_wait):
        def categorize_queue(q):
            if q < 3: return "Low"
            elif q <= 5: return "Medium"
            else: return "High"
            
        we_q = categorize_queue(we_queue)
        ns_q = categorize_queue(ns_queue)
        starving = "Starving" if (we_max_wait > 100.0 or ns_max_wait > 100.0) else "NoStarvation"
        return f"{we_q}*{ns_q}*{starving}"

    def get_action(self, state, evaluate=False):
        if state not in self.q_table:
            self.q_table[state] = [0.0] * 9
            
        if not evaluate and random.uniform(0, 1) < self.epsilon:
            return random.choice(range(len(self.actions)))
        else:
            return self.q_table[state].index(max(self.q_table[state]))

    def get_metrics(self):
        we_vehs = traci.edge.getLastStepVehicleIDs("E0")
        ns_vehs = traci.edge.getLastStepVehicleIDs("E1")
        
        we_queue = traci.edge.getLastStepHaltingNumber("E0")
        ns_queue = traci.edge.getLastStepHaltingNumber("E1")
        
        we_max_wait = max([traci.vehicle.getWaitingTime(v) for v in we_vehs]) if we_vehs else 0.0
        ns_max_wait = max([traci.vehicle.getWaitingTime(v) for v in ns_vehs]) if ns_vehs else 0.0
        
        total_wait = sum([traci.vehicle.getWaitingTime(v) for v in we_vehs]) + sum([traci.vehicle.getWaitingTime(v) for v in ns_vehs])
        total_queue = we_queue + ns_queue
        
        return we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue

    def run_cycle(self, action_idx):
        we_green, ns_green = self.actions[action_idx]
        arrived = 0
        steps = 0
        
        # WE Green
        traci.trafficlight.setPhase("J2", 0)
        for _ in range(we_green):
            traci.simulationStep()
            arrived += traci.simulation.getArrivedNumber()
            steps += 1
            if traci.simulation.getMinExpectedNumber() == 0: return arrived, steps
            
        # WE Yellow
        traci.trafficlight.setPhase("J2", 1)
        for _ in range(3):
            traci.simulationStep()
            arrived += traci.simulation.getArrivedNumber()
            steps += 1
            if traci.simulation.getMinExpectedNumber() == 0: return arrived, steps
            
        # NS Green
        traci.trafficlight.setPhase("J2", 2)
        for _ in range(ns_green):
            traci.simulationStep()
            arrived += traci.simulation.getArrivedNumber()
            steps += 1
            if traci.simulation.getMinExpectedNumber() == 0: return arrived, steps
            
        # NS Yellow
        traci.trafficlight.setPhase("J2", 3)
        for _ in range(3):
            traci.simulationStep()
            arrived += traci.simulation.getArrivedNumber()
            steps += 1
            if traci.simulation.getMinExpectedNumber() == 0: return arrived, steps
            
        return arrived, steps

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', type=int, default=0)
    parser.add_argument('--evaluate', type=int, default=0)
    parser.add_argument('--scenario', type=str, default="sumofiles/routes/s3_heavy_asym_1200.rou.xml")
    parser.add_argument('--gui', action='store_true')
    args = parser.parse_args()

    base_dir = Path(r"C:\VSCODE\CISInternship_Implement")
    os.chdir(base_dir)

    agent = QLearningAgent()
    
    if os.path.exists("src/q_table.json"):
        agent.load_q_table("src/q_table.json")

    os.makedirs("outputs", exist_ok=True)
    
    episodes = args.train if args.train > 0 else args.evaluate
    evaluate_mode = args.evaluate > 0
    
    if evaluate_mode:
        agent.epsilon = 0.0

    print("="*60)
    print("STEP 3: Q-LEARNING AGENT EXECUTION")
    print("="*60)
    print(f"Mode: {'Evaluate' if evaluate_mode else 'Train'}")
    print(f"Episodes: {episodes}")
    print(f"Scenario: {args.scenario}")
    
    decision_log_path = f"outputs/decision_log.csv"
    episode_log_path = f"outputs/training_episode_summary.csv"
    
    with open(decision_log_path, "w", newline='') as d_file, open(episode_log_path, "w", newline='') as e_file:
        d_writer = csv.writer(d_file)
        d_writer.writerow(["Episode", "Decision", "State", "Action", "Next_State", "WE_Wait", "NS_Wait", "WE_Queue", "NS_Queue", "Total_Wait", "Total_Queue", "Throughput_Rate", "W_q", "T_q", "Q_q", "Reward", "Q_before", "Q_after"])
        
        e_writer = csv.writer(e_file)
        e_writer.writerow(["Episode", "Total_Reward", "Epsilon", "Steps"])
        
        decision = 0
        for ep in range(episodes):
            sumo_binary = "sumo-gui" if args.gui else "sumo"
            sumo_cmd = [sumo_binary, "-n", "sumofiles/Traci.net.xml", "-r", args.scenario, "--no-warnings"]
            traci.start(sumo_cmd)
            
            ep_reward = 0
            ep_steps = 0
            
            we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
            state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
            
            while traci.simulation.getMinExpectedNumber() > 0:
                action_idx = agent.get_action(state, evaluate=evaluate_mode)
                q_before = agent.q_table[state][action_idx]
                
                arrived, steps = agent.run_cycle(action_idx)
                ep_steps += steps
                
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
                    
                we_queue, ns_queue, we_max_wait, ns_max_wait, total_wait, total_queue = agent.get_metrics()
                next_state = agent.get_state(we_queue, ns_queue, we_max_wait, ns_max_wait)
                
                T = arrived / steps if steps > 0 else 0
                
                W_q = agent._normalize(total_wait, agent.bounds["W_min"], agent.bounds["W_max"], invert=True)
                Q_q = agent._normalize(total_queue, agent.bounds["Q_min"], agent.bounds["Q_max"], invert=True)
                T_q = agent._normalize(T, agent.bounds["T_min"], agent.bounds["T_max"], invert=False)
                P_s = 2.0 if (we_max_wait > 100.0 or ns_max_wait > 100.0) else 0.0
                
                reward = 0.50 * W_q + 0.30 * T_q + 0.20 * Q_q - P_s
                
                if next_state not in agent.q_table:
                    agent.q_table[next_state] = [0.0, 0.0, 0.0, 0.0]
                    
                if not evaluate_mode:
                    agent.q_table[state][action_idx] = q_before + agent.alpha * (reward + agent.gamma * max(agent.q_table[next_state]) - q_before)
                q_after = agent.q_table[state][action_idx]
                
                ep_reward += reward
                
                d_writer.writerow([ep+1, decision, state, agent.actions[action_idx], next_state, f"{we_max_wait:.2f}", f"{ns_max_wait:.2f}", we_queue, ns_queue, f"{total_wait:.2f}", total_queue, f"{T:.4f}", f"{W_q:.4f}", f"{T_q:.4f}", f"{Q_q:.4f}", f"{reward:.4f}", f"{q_before:.4f}", f"{q_after:.4f}"])
                decision += 1
                state = next_state
                
            traci.close()
            e_writer.writerow([ep+1, f"{ep_reward:.4f}", f"{agent.epsilon:.4f}", ep_steps])
            print(f"Episode {ep+1}/{episodes} completed. Reward: {ep_reward:.2f}, Epsilon: {agent.epsilon:.4f}, Steps: {ep_steps}")
            
            if not evaluate_mode:
                agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)
                
    if not evaluate_mode:
        agent.save_q_table("src/q_table.json")
        print("Q-Table saved to src/q_table.json")
        
    print("STATUS: AUDIT COMPLETE")

if __name__ == '__main__':
    main()
