import pandas as pd

def check_littles_law(file_path, total_cars):
    df = pd.read_csv(file_path)
    total_queue = (df['Queue_West_East'] + df['Queue_North_South']).sum()
    avg_wait = total_queue * 1.0 / total_cars
    print(f"{file_path}:")
    print(f"  Total Queue (Total Wait Time): {total_queue}")
    print(f"  Avg Wait per car (Little's Law): {avg_wait:.2f}")

# Fixed time 200
check_littles_law('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_10s_cars_200total_1000s_unbalanced.csv', 200)
check_littles_law('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_45s_cars_200total_1000s_unbalanced.csv', 200)

# Fixed time 1200
check_littles_law('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_10s_cars_1200total_1000s_unbalanced.csv', 1200)
check_littles_law('c:/VSCODE/CISInternship_Implement/collected_data/metrics_dur_45s_cars_1200total_1000s_unbalanced.csv', 1200)

