import os
import sys
import pandas as pd
import io

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "outputs")

def main():
    print("--- STARTING DATA ANALYSIS ---")
    
    # 1. Load Evaluation Matrix
    eval_path = os.path.join(OUTPUT_DIR, "evaluation_comparison_matrix.csv")
    if os.path.exists(eval_path):
        eval_df = pd.read_csv(eval_path)
    else:
        print(f"File not found: {eval_path}")
        return

    # 2. Extract Agent logs from mixed decision_log
    dec_path = os.path.join(OUTPUT_DIR, "decision_log.csv")
    valid_lines = []
    headers = "episode,decision_step,scenario,state,action,next_state,we_wait,ns_wait,total_wait,we_queue,ns_queue,total_queue,transition_throughput,reward,q_before,q_after"
    valid_lines.append(headers)
    
    with open(dec_path, 'r') as f:
        for line in f:
            if ".rou.xml" in line:
                valid_lines.append(line.strip())
                
    dec_df = pd.read_csv(io.StringIO("\n".join(valid_lines)))

    # Insight 1: Policy Behavior
    print("\n--- Insight 1: Policy Behavior (Action Distribution by Scenario) ---")
    action_dist = dec_df.groupby(['scenario', 'action']).size().unstack(fill_value=0)
    action_dist_pct = action_dist.div(action_dist.sum(axis=1), axis=0) * 100
    print(action_dist_pct.round(2).to_string())

    # Insight 2: Directional Split (WE vs NS)
    print("\n--- Insight 2: Directional Split Analysis ---")
    dir_metrics = dec_df.groupby('scenario')[['we_wait', 'ns_wait', 'we_queue', 'ns_queue']].mean()
    print(dir_metrics.round(2).to_string())
    
    # Insight 3: Starvation Protection Check
    print("\n--- Insight 3: Starvation Event Check ---")
    starvation_events = eval_df[eval_df['Policy'] == 'RL_Agent']['Starvations'].sum()
    print(f"Total RL Agent Starvations Across Scenarios: {starvation_events}")

if __name__ == "__main__":
    main()
