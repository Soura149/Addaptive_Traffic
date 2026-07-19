import pandas as pd
import os

def main():
    # Define the files and their corresponding car tiers
    files = {
        'sumofiles/eval_variation_200.csv': '200',
        'sumofiles/eval_variation_400.csv': '400',
        'sumofiles/eval_variation_800.csv': '800',
        'sumofiles/evaluation_log.csv': '1200'
    }

    results = []

    for filepath, tier in files.items():
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            
            # Check if necessary columns exist
            required_cols = ['we_queue', 'ns_queue', 'we_waiting_time', 'ns_waiting_time']
            if all(col in df.columns for col in required_cols):
                max_we = df['we_queue'].max()
                max_ns = df['ns_queue'].max()
                mean_wait = (df['we_waiting_time'] + df['ns_waiting_time']).mean()
                total_rows = len(df)
                
                results.append({
                    'Car Tier': tier,
                    'Max WE Queue': max_we,
                    'Max NS Queue': max_ns,
                    'Mean Waiting Time': mean_wait,
                    'Total Rows': total_rows
                })
            else:
                print(f"Missing required columns in {filepath}")
        else:
            print(f"File not found: {filepath}")

    if not results:
        print("No data was processed.")
        return

    # Create a DataFrame from the results
    compiled_df = pd.DataFrame(results)
    
    # Save to CSV
    output_path = 'sumofiles/compiled_agent_metrics.csv'
    compiled_df.to_csv(output_path, index=False)
    
    # Print clearly to console
    print("\n=== Compiled Agent Metrics ===")
    print(compiled_df.to_string(index=False))
    print("==============================\n")
    print(f"Compiled metrics saved to: {output_path}")

if __name__ == "__main__":
    main()
