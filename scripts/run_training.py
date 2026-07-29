import os
import sys

base_dir = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"
sys.path.append(base_dir)

from src.q_learning_agent import QLearningAgent

def run_training():
    print("Initializing Step 4: Multi-Demand Curriculum Q-Learning Agent Training...")
    
    # Initialize Agent with user-specified hyperparameters
    agent = QLearningAgent(alpha=0.1, gamma=0.9, epsilon=1.0, epsilon_decay=0.95, min_epsilon=0.05)
    
    # Setup the 25 scenario files in a systematic cycle
    vols = [100, 300, 600, 900, 1200]
    scenarios = []
    for we_vol in vols:
        for ns_vol in vols:
            filename = f"route_we_{we_vol}_ns_{ns_vol}.rou.xml"
            scenarios.append(filename)
            
    total_episodes = 500
    
    for episode in range(1, total_episodes + 1):
        # Systematically cycle through the 25 scenarios
        scenario_idx = (episode - 1) % len(scenarios)
        scenario_filename = scenarios[scenario_idx]
        route_path = os.path.join(base_dir, "sumofiles", "routes", scenario_filename)
        
        # Run episode in headless mode
        total_reward = agent.run_training_episode(episode, scenario_filename, route_path, use_gui=False)
        
        # Log to console periodically or every episode to show progress
        print(f"Episode {episode:03d}/500 | Scenario: {scenario_filename:<25} | Reward: {total_reward:7.2f} | Epsilon: {agent.epsilon:.4f}")
        
    # Save Final Q-Table
    agent.save_q_table()
    
    # Report generation
    print("\nTraining completed successfully.")
    print("Files updated:")
    print(" - outputs/decision_log.csv")
    print(" - outputs/training_summary.csv")
    print(" - outputs/q_table.json")

if __name__ == "__main__":
    run_training()
