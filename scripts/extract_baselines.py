import pandas as pd
import os

def main():
    base_dir = "collected_data"
    tiers = [200, 400, 800, 1200]
    durations = [10, 20, 30, 45]
    rl_agent_times = [42.25, 100.53, 126.63, 131.71]
    
    results = []
    
    for i, tier in enumerate(tiers):
        row = {'Volume Tier': f"{tier} Cars"}
        
        for dur in durations:
            filename = f"metrics_dur_{dur}s_cars_{tier}total_1000s_unbalanced.csv"
            filepath = os.path.join(base_dir, filename)
            
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                # Calculating the total average waiting time for the step
                mean_wait = (df['Avg_Waiting_Time_West_East'] + df['Avg_Waiting_Time_North_South']).mean()
                row[f'Baseline {dur}s'] = round(mean_wait, 2)
            else:
                row[f'Baseline {dur}s'] = "N/A"
                
        row['RL Agent'] = rl_agent_times[i]
        results.append(row)
        
    compiled_df = pd.DataFrame(results)
    
    print("\n=== Baseline vs RL Agent Average Waiting Times (Unbalanced Traffic) ===")
    print(compiled_df.to_string(index=False))
    print("=======================================================================\n")

if __name__ == "__main__":
    main()
