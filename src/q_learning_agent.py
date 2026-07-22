import os
import sys
import json
import random
import csv

# Add SUMO tools
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    # Ensure this doesn't crash during unit test if SUMO_HOME is missing, just skip traci import
    pass

try:
    import traci
    from sumolib import checkBinary
except ImportError:
    pass

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class QLearningAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0, epsilon_decay=0.995, min_epsilon=0.01):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.actions = [10, 20, 30, 45]
        self.q_table = {}
        
        self.bounds = self.load_calibration_bounds()
        
        self.decision_log_path = os.path.join(OUTPUT_DIR, "decision_log.csv")
        self.summary_log_path = os.path.join(OUTPUT_DIR, "training_summary.csv")
        self.q_table_path = os.path.join(OUTPUT_DIR, "q_table.json")
        
        self._init_logs()

    def _init_logs(self):
        if not os.path.exists(self.decision_log_path):
            with open(self.decision_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["episode", "decision_step", "scenario", "state", "action", "next_state", "we_wait", "ns_wait", "total_wait", "we_queue", "ns_queue", "total_queue", "transition_throughput", "reward", "q_before", "q_after"])
        
        if not os.path.exists(self.summary_log_path):
            with open(self.summary_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["episode", "scenario", "total_reward", "avg_queue", "avg_wait", "total_throughput"])

    def load_calibration_bounds(self):
        bounds_path = os.path.join(WORKSPACE_DIR, "src", "calibration_bounds.json")
        if not os.path.exists(bounds_path):
            print(f"Warning: Bounds file not found at {bounds_path}. Using default bounds.")
            return {"W_min": 0, "W_max": 300, "Q_min": 0, "Q_max": 10, "T_min": 0, "T_max": 1.0}
        
        with open(bounds_path, 'r') as f:
            bounds = json.load(f)
        return bounds

    def _get_queue_level(self, q):
        if q < 5:
            return "Low"
        elif q < 15:
            return "Medium"
        else:
            return "High"

    def get_state(self, we_queue, ns_queue, we_wait, ns_wait):
        we_level = self._get_queue_level(we_queue)
        ns_level = self._get_queue_level(ns_queue)
        
        we_starving = we_wait > 100.0
        ns_starving = ns_wait > 100.0
        
        if we_starving and ns_starving:
            starvation = "Both_Starving"
        elif we_starving:
            starvation = "WE_Starving"
        elif ns_starving:
            starvation = "NS_Starving"
        else:
            starvation = "NoStarvation"
            
        return f"{we_level}_{ns_level}_{starvation}"

    def calculate_reward(self, T, W, Q, we_wait, ns_wait):
        def _normalize(val, min_val, max_val, invert=False):
            if max_val == min_val:
                return 0.5
            norm = (val - min_val) / (max_val - min_val)
            if invert:
                norm = 1.0 - norm
            # Clip between 0 and 1
            return max(0.0, min(1.0, norm))
            
        T_q = _normalize(T, self.bounds['T_min'], self.bounds['T_max'], invert=False)
        W_q = _normalize(W, self.bounds['W_min'], self.bounds['W_max'], invert=True)
        Q_q = _normalize(Q, self.bounds['Q_min'], self.bounds['Q_max'], invert=True)
        
        P_s = 2.0 if max(we_wait, ns_wait) > 100.0 else 0.0
        
        R = 0.50 * T_q + 0.30 * W_q + 0.20 * Q_q - P_s
        return R

    def choose_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = {str(a): 0.0 for a in self.actions}
            
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.actions)
        else:
            # max Q
            q_vals = self.q_table[state]
            return int(max(q_vals, key=q_vals.get))

    def update_q_value(self, state, action, reward, next_state):
        if state not in self.q_table:
            self.q_table[state] = {str(a): 0.0 for a in self.actions}
        if next_state not in self.q_table:
            self.q_table[next_state] = {str(a): 0.0 for a in self.actions}
            
        action_str = str(action)
        q_before = self.q_table[state][action_str]
        
        max_next_q = max(self.q_table[next_state].values())
        new_q = q_before + self.alpha * (reward + self.gamma * max_next_q - q_before)
        
        self.q_table[state][action_str] = new_q
        
        return q_before, new_q

    def save_q_table(self):
        with open(self.q_table_path, 'w') as f:
            json.dump(self.q_table, f, indent=4)

    def log_decision(self, episode, step, scenario, state, action, next_state, we_w, ns_w, t_w, we_q, ns_q, t_q, t_rate, r, q_b, q_a):
        with open(self.decision_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([episode, step, scenario, state, action, next_state, we_w, ns_w, t_w, we_q, ns_q, t_q, t_rate, r, q_b, q_a])

    def log_summary(self, episode, scenario, total_r, avg_q, avg_w, total_t):
        with open(self.summary_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([episode, scenario, total_r, avg_q, avg_w, total_t])

    def run_training_episode(self, episode, scenario_name, route_path, use_gui=False):
        net_path = os.path.join(WORKSPACE_DIR, "sumofiles", "Traci.net.xml")
        
        sumo_binary = checkBinary('sumo-gui') if use_gui else checkBinary('sumo')
        cmd = [sumo_binary, "-n", net_path, "-r", route_path, "--no-step-log", "true", "--no-warnings", "true", "--time-to-teleport", "-1"]
        
        traci.start(cmd)
        
        we_edges = ["E0"]
        ns_edges = ["E1"]
        
        def get_metrics():
            we_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in we_edges)
            ns_q = sum(traci.edge.getLastStepHaltingNumber(e) for e in ns_edges)
            we_w = sum(traci.edge.getWaitingTime(e) for e in we_edges)
            ns_w = sum(traci.edge.getWaitingTime(e) for e in ns_edges)
            return we_q, ns_q, we_q + ns_q, we_w, ns_w, we_w + ns_w
            
        step = 0
        total_reward = 0
        sum_q = 0
        sum_w = 0
        total_throughput = 0
        decisions = 0
        
        current_phase = 0 # 0 for WE, 2 for NS
        
        # Initial state
        we_q, ns_q, t_q, we_w, ns_w, t_w = get_metrics()
        state = self.get_state(we_q, ns_q, we_w, ns_w)
        
        while traci.simulation.getMinExpectedNumber() > 0:
            action = self.choose_action(state)
            
            traci.trafficlight.setPhase("J2", current_phase)
            
            arrived = 0
            for _ in range(action):
                traci.simulationStep()
                arrived += traci.simulation.getArrivedNumber()
                step += 1
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
                    
            t_rate = arrived / action
            total_throughput += arrived
            
            next_we_q, next_ns_q, next_t_q, next_we_w, next_ns_w, next_t_w = get_metrics()
            next_state = self.get_state(next_we_q, next_ns_q, next_we_w, next_ns_w)
            
            reward = self.calculate_reward(t_rate, next_t_w, next_t_q, next_we_w, next_ns_w)
            
            q_b, q_a = self.update_q_value(state, action, reward, next_state)
            
            self.log_decision(episode, decisions, scenario_name, state, action, next_state, next_we_w, next_ns_w, next_t_w, next_we_q, next_ns_q, next_t_q, t_rate, reward, q_b, q_a)
            
            total_reward += reward
            sum_q += next_t_q
            sum_w += next_t_w
            decisions += 1
            
            state = next_state
            
            if traci.simulation.getMinExpectedNumber() == 0:
                break
                
            # Yellow Phase
            traci.trafficlight.setPhase("J2", current_phase + 1)
            for _ in range(3):
                traci.simulationStep()
                step += 1
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
                    
            current_phase = 2 if current_phase == 0 else 0
            
        traci.close()
        
        avg_q = sum_q / decisions if decisions > 0 else 0
        avg_w = sum_w / decisions if decisions > 0 else 0
        
        self.log_summary(episode, scenario_name, total_reward, avg_q, avg_w, total_throughput)
        
        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        return total_reward

if __name__ == "__main__":
    pass
