import pandas as pd

def check_mean_total_wait(file_path):
    df = pd.read_csv(file_path)
    # wait_time = avg_wait_time * queue
    df['total_wait_time_we'] = df['Avg_Waiting_Time_West_East'] * df['Queue_West_East']
    df['total_wait_time_ns'] = df['Avg_Waiting_Time_North_South'] * df['Queue_North_South']
    df['total_wait_time'] = df['total_wait_time_we'] + df['total_wait_time_ns']
    
    mean_wait = df['total_wait_time'].mean()
    print(f"{file_path}:")
    print(f"  Mean Total Wait Time per step: {mean_wait:.2f}")

# Fixed time 200
check_mean_total_wait('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_10s_cars_200total_1000s_unbalanced.csv')
check_mean_total_wait('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_45s_cars_200total_1000s_unbalanced.csv')

# Fixed time 1200
check_mean_total_wait('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_10s_cars_1200total_1000s_unbalanced.csv')
check_mean_total_wait('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_45s_cars_1200total_1000s_unbalanced.csv')

