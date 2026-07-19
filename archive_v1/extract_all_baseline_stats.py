import pandas as pd
import os

def main():
    base_dir = "collected_data"
    tiers = [200, 400, 800, 1200]
    durations = [10, 20, 30, 45]
    
    results = []
    
    for tier in tiers:
        for dur in durations:
            filename = f"metrics_dur_{dur}s_cars_{tier}total_1000s_unbalanced.csv"
            filepath = os.path.join(base_dir, filename)
            
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                
                # Baseline files use 'Queue_West_East' for the queue length
                if 'Queue_West_East' in df.columns:
                    max_we = df['Queue_West_East'].max()
                    std_we = df['Queue_West_East'].std()
                    
                    if pd.isna(std_we):
                        std_we = 0.0
                else:
                    max_we = "N/A"
                    std_we = "N/A"
                    
                results.append({
                    'Volume Tier': f"{tier}",
                    'Strategy': f"Fixed {dur}s",
                    'Max WE Queue': max_we,
                    'WE Queue SD': round(std_we, 2) if isinstance(std_we, float) else std_we
                })
            else:
                results.append({
                    'Volume Tier': f"{tier}",
                    'Strategy': f"Fixed {dur}s",
                    'Max WE Queue': "Missing",
                    'WE Queue SD': "N/A"
                })
                
    compiled_df = pd.DataFrame(results)
    
    print("\n=== Baseline Queue Structural Metrics ===")
    print(compiled_df.to_string(index=False))
    print("=========================================\n")

if __name__ == "__main__":
    main()
