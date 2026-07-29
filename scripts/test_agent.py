import sys
import os
import random
import json

base_dir = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"
sys.path.append(base_dir)

from src.q_learning_agent import QLearningAgent

def run_tests():
    print("--- QLearningAgent (Pure Phase Control) Unit Tests ---")
    
    agent = QLearningAgent()
    
    # Test 1: Action space [0, 1]
    print("\n[Test 1] Action Space")
    assert agent.actions == [0, 1], f"Expected [0, 1], got {agent.actions}"
    print("PASS: Action space is exactly [0, 1].")
    
    # Test 2: State representation
    print("\n[Test 2] State Formatting")
    state = agent.get_state(we_queue=2, ns_queue=8, we_wait=50, ns_wait=60)
    assert state == "Low*Medium*NoStarvation", f"Got: {state}"
    print("PASS: State string generated without current phase.")
    
    # Test 3: Q-Table Array Structure
    print("\n[Test 3] Q-Table Value Initialization and Export")
    agent.update_q_value(state, action=1, reward=1.5, next_state="Medium*Low*NoStarvation")
    assert isinstance(agent.q_table[state], list)
    assert len(agent.q_table[state]) == 2
    
    # Ensure export generates correctly
    agent.save_q_table()
    with open(agent.q_table_path, 'r') as f:
        data = json.load(f)
    assert isinstance(data[state], list)
    print("PASS: Q-table saved gracefully as array lists per state key.")

    print("\n--- ALL TESTS PASSED ---")

if __name__ == "__main__":
    run_tests()
