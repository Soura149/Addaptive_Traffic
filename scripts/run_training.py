import os
import sys
import random
import csv

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_DIR, "src"))

from q_learning_agent import QLearningAgent

SCENARIOS = [
    "s1_low_200.rou.xml",
    "s2_medium_600.rou.xml",
    "s3_heavy_asym_1200.rou.xml",
    "s4_heavy_sym_1200.rou.xml",
    "s5_peak_1800.rou.xml"
]

def main():
    print("Initializing Multi-Demand Q-Learning Agent Training...")
    
    agent = QLearningAgent(
        alpha=0.1, 
        gamma=0.9, 
        epsilon=1.0, 
        epsilon_decay=0.95, 
        min_epsilon=0.05
    )
    
    episodes = 50
    print(f"Training for {episodes} episodes over {len(SCENARIOS)} scenarios.")
    
    for ep in range(1, episodes + 1):
        # Systematically rotate or randomly select
        scenario = random.choice(SCENARIOS)
        route_path = os.path.join(WORKSPACE_DIR, "sumofiles", "routes", scenario)
        
        print(f"Episode {ep}/{episodes} | Scenario: {scenario} | Epsilon: {agent.epsilon:.3f}")
        
        total_reward = agent.run_training_episode(
            episode=ep,
            scenario_name=scenario,
            route_path=route_path,
            use_gui=False
        )
        
        print(f"  -> Episode {ep} completed. Total Reward: {total_reward:.2f}")

    # Save Q-table at the end
    agent.save_q_table()
    print(f"Training complete. Q-Table saved to {agent.q_table_path}")
    print(f"Decision Log saved to {agent.decision_log_path}")
    print(f"Summary Log saved to {agent.summary_log_path}")

if __name__ == "__main__":
    main()
