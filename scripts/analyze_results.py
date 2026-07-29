import os
import csv
from collections import Counter

base_dir = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"
decision_log_path = os.path.join(base_dir, "outputs", "decision_log.csv")
eval_matrix_path = os.path.join(base_dir, "outputs", "evaluation_comparison_matrix.csv")

def analyze_results():
    print("--- Step 6 Analytical Insight Extraction ---")
    
    # 1. Action Selection Analysis (Extracting from decision_log)
    action_counts = {
        "Heavy WE Asymmetric": Counter(),
        "Heavy NS Asymmetric": Counter(),
        "Peak Gridlock": Counter()
    }
    
    if os.path.exists(decision_log_path):
        with open(decision_log_path, 'r') as f:
            reader = csv.DictReader(f)
            # Only analyze late exploitation episodes (e.g. > 80)
            for row in reader:
                ep = int(row['episode'])
                if ep > 80:
                    scenario = row['scenario']
                    action = row['action']
                    if 'we_900_ns_300' in scenario:
                        action_counts["Heavy WE Asymmetric"][action] += 1
                    elif 'we_300_ns_900' in scenario:
                        action_counts["Heavy NS Asymmetric"][action] += 1
                    elif 'we_1200_ns_1200' in scenario:
                        action_counts["Peak Gridlock"][action] += 1
                        
        print("\n[Policy Asymmetry & Action Selection - Episodes > 80]")
        for profile, counts in action_counts.items():
            if counts:
                most_common = counts.most_common(3)
                print(f"Profile: {profile}")
                for act, freq in most_common:
                    print(f"   Action: {act} -> Frequency: {freq}")
    else:
        print("Decision log not found.")

    # 2. Waiting Time & Bias Fairness Analysis (Extracting from eval_matrix)
    print("\n[Waiting Time Minimization & Directional Fairness]")
    if os.path.exists(eval_matrix_path):
        with open(eval_matrix_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Model'] == 'RL Agent':
                    print(f"Scenario: {row['Scenario']:<20} | Avg Wait: {row['Average Wait (s)']:>6}s | Starvation: {row['Starvation Events']}")
    else:
        print("Evaluation matrix not found.")

if __name__ == "__main__":
    analyze_results()
