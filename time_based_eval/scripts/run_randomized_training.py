import os
import sys
import random
from pathlib import Path

# Add src to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from q_learning_agent import QLearningAgent

def generate_continuous_route(route_file_path, duration, prob_we, prob_ns):
    with open(route_file_path, "w") as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        f.write('    <vType id="car" maxSpeed="13.89" length="4.7"/>\n')
        f.write('    <route id="route_we" edges="E0 E0.58"/>\n')
        f.write('    <route id="route_ns" edges="E1 E2"/>\n')
        f.write(f'    <flow id="flow_we" type="car" route="route_we" begin="0" end="{duration}" probability="{prob_we}" departLane="0"/>\n')
        f.write(f'    <flow id="flow_ns" type="car" route="route_ns" begin="0" end="{duration}" probability="{prob_ns}" departLane="0"/>\n')
        f.write('</routes>\n')

def main():
    base_dir = Path(r"C:\VSCODE\CISInternship_Implement")
    os.chdir(base_dir)

    os.makedirs("outputs", exist_ok=True)
    
    agent = QLearningAgent(alpha=0.1, epsilon=1.0) # Start with high exploration
    agent.q_table_path = "outputs/universal_q_table.json"
    
    print("="*80)
    print("UNIVERSAL RANDOMIZED TRAINING (100 EPISODES)")
    print("="*80)
    
    route_path = "sumofiles/routes/continuous_flow.rou.xml"
    
    for ep in range(1, 101):
        # Generate random traffic for this episode
        is_symmetric = random.random() < 0.5
        if is_symmetric:
            shared_prob = round(random.uniform(0.1, 0.7), 2)
            we_prob = ns_prob = shared_prob
            profile = f"SYM ({int(shared_prob*100)}%)"
        else:
            prob1 = round(random.uniform(0.4, 0.8), 2)
            prob2 = round(random.uniform(0.05, 0.3), 2)
            if random.random() < 0.5:
                we_prob, ns_prob = prob1, prob2
            else:
                we_prob, ns_prob = prob2, prob1
            profile = f"ASYM (W:{int(we_prob*100)}% N:{int(ns_prob*100)}%)"

        generate_continuous_route(route_path, 1800, we_prob, ns_prob)
        
        # Run episode
        total_reward = agent.run_training_episode(ep, profile, route_path, use_gui=False)
        print(f"Ep {ep:<3} [{profile:<20}] | Total Reward: {total_reward:>7.4f} | Eps: {agent.epsilon:.4f}")
        
        agent.save_q_table()
            
    visited_states = len(agent.q_table)
    
    print("\n" + "="*80)
    print("TRAINING COMPLETION SUMMARY")
    print("="*80)
    print(f"Total Episodes Run: 100")
    print(f"Total Unique States Visited: {visited_states}")
    print(f"Final Universal Q-Table saved to outputs/universal_q_table.json")
    print("STATUS: UNIVERSAL TRAINING COMPLETE")

if __name__ == '__main__':
    main()
