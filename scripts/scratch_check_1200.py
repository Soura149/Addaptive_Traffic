import pandas as pd

def check_baseline(file_path):
    df = pd.read_csv(file_path)
    mean_we = df['Avg_Waiting_Time_West_East'].mean()
    mean_ns = df['Avg_Waiting_Time_North_South'].mean()
    mean_total_avg = mean_we + mean_ns
    wait_time_we_approx = (df['Avg_Waiting_Time_West_East'] * df['Queue_West_East']).mean()
    wait_time_ns_approx = (df['Avg_Waiting_Time_North_South'] * df['Queue_North_South']).mean()
    
    print(f"{file_path}:")
    print(f"  Mean Avg_Wait (WE+NS): {mean_total_avg:.2f}")
    print(f"  Approx Total Wait (WE+NS): {(wait_time_we_approx + wait_time_ns_approx):.2f}")

def check_rl(file_path):
    df = pd.read_csv(file_path)
    if 'we_waiting_time' in df.columns:
        mean_we = df['we_waiting_time'].mean()
        mean_ns = df['ns_waiting_time'].mean()
    else:
        mean_we = 0
        mean_ns = 0
    print(f"{file_path}:")
    print(f"  Mean Total Wait (WE+NS): {(mean_we + mean_ns):.2f}")

# Check fixed times 1200
check_baseline('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_10s_cars_1200total_1000s_unbalanced.csv')
check_baseline('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_45s_cars_1200total_1000s_unbalanced.csv')

# Check RL 1200
check_rl('c:/VSCODE/CISInternship_Implement/sumofiles/evaluation_log.csv')
