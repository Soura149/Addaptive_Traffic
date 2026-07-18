import pandas as pd
import os

def main():
    files = {
        'sumofiles/eval_variation_200.csv': '200 Cars',
        'sumofiles/eval_variation_400.csv': '400 Cars',
        'sumofiles/eval_variation_800.csv': '800 Cars',
        'sumofiles/evaluation_log.csv': '1200 Cars'
    }
    
    results = []
    
    for filepath, tier in files.items():
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            
            # Extract metrics
            if 'we_waiting_time' in df.columns and 'ns_waiting_time' in df.columns:
                mean_wait = (df['we_waiting_time'] + df['ns_waiting_time']).mean()
            else:
                mean_wait = None
                
            max_we_queue = df['we_queue'].max()
            max_ns_queue = df['ns_queue'].max()
            
            std_we_queue = df['we_queue'].std()
            std_ns_queue = df['ns_queue'].std()
            
            # Fill NaN with 0 if calculation yields NaN (e.g. standard deviation of 1 item)
            if pd.isna(std_we_queue): std_we_queue = 0
            if pd.isna(std_ns_queue): std_ns_queue = 0
            
            results.append({
                'Volume Tier': tier,
                'Mean Wait': round(mean_wait, 2) if mean_wait is not None else "N/A",
                'Max WE Queue': max_we_queue,
                'Max NS Queue': max_ns_queue,
                'WE Queue SD': round(std_we_queue, 2),
                'NS Queue SD': round(std_ns_queue, 2)
            })
        else:
            print(f"Warning: File not found: {filepath}")
            
    compiled_df = pd.DataFrame(results)
    
    print("\n=== Agent Evaluation Statistics ===")
    print(compiled_df.to_string(index=False))
    print("===================================\n")

if __name__ == "__main__":
    main()
