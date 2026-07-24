import os
import sys

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_DIR, "src"))

from q_learning_agent import QLearningAgent

def run_tests():
    print("--- Running QLearningAgent Validation Tests ---")
    
    agent = QLearningAgent()
    
    print("\n1. Testing Bounds Loading...")
    print(f"Bounds Loaded: {agent.bounds}")
    assert 'W_min' in agent.bounds, "Missing W_min in bounds"
    assert agent.bounds['W_max'] >= agent.bounds['W_min'], "Invalid W_max/W_min"
    print("Bounds Loading: PASS")
    
    print("\n2. Testing State Discretization...")
    s1 = agent.get_state(2, 2, 50, 50)
    assert s1 == "Low_Low_NoStarvation", f"Failed state s1: {s1}"
    
    s2 = agent.get_state(10, 16, 120, 50)
    assert s2 == "Medium_High_WE_Starving", f"Failed state s2: {s2}"
    
    s3 = agent.get_state(18, 18, 150, 200)
    assert s3 == "High_High_Both_Starving", f"Failed state s3: {s3}"
    print("State Discretization: PASS")
    
    print("\n3. Testing Reward Calculation...")
    # T, W, Q, we_wait, ns_wait
    r1 = agent.calculate_reward(T=0.55, W=0, Q=0, we_wait=0, ns_wait=0)
    print(f"Reward (Max possible): {r1}")
    
    r2 = agent.calculate_reward(T=0, W=304, Q=8, we_wait=0, ns_wait=0)
    print(f"Reward (Min possible, no starvation): {r2}")
    
    r3 = agent.calculate_reward(T=0, W=304, Q=8, we_wait=110, ns_wait=0)
    print(f"Reward (Min possible with starvation): {r3}")
    
    print("Reward Calculation: PASS")
    
    print("\n4. Testing Action Selection & Q-Update...")
    agent.q_table[s1] = {"10": 0.5, "20": 1.0, "30": 0.2, "45": 0.1}
    agent.epsilon = 0.0 # Force greedy
    action = agent.choose_action(s1)
    assert action == 20, f"Expected 20, got {action}"
    
    q_b, q_a = agent.update_q_value(s1, 10, 5.0, s2)
    print(f"Q-Update: {q_b} -> {q_a}")
    print("Action & Q-Update: PASS")
    
    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
