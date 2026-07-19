import pandas as pd
import numpy as np

import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "new_experiment_analytics")

files = {
    '10s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_10s.csv'),
    '20s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_20s.csv'),
    '30s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_30s.csv'),
    '45s Fixed Baseline': os.path.join(DATA_DIR, 'baseline_45s.csv')
}

print(f"{'Agent / Baseline':<20} | {'Avg Wait (s)':<12} | {'Max Queue (veh)':<15} | {'Cumulative Throughput':<22}")
print("-" * 75)

# Baselines
for name, f in files.items():
    df = pd.read_csv(f)
    avg_wait = (df['we_waiting_time'].mean() + df['ns_waiting_time'].mean()) / 2
    max_queue = max(df['we_queue'].max(), df['ns_queue'].max())
    throughput = df['completed_vehicles'].sum()
    print(f"{name:<20} | {avg_wait:<12.2f} | {max_queue:<15.0f} | {throughput:<22.0f}")

# RL Agent
df_eval = pd.read_csv(os.path.join(DATA_DIR, 'evaluation_log.csv'))
episodes = df_eval['episode'].unique()
avg_wait_list = []
max_queue_list = []
throughput_list = []

for ep in episodes:
    ep_df = df_eval[df_eval['episode'] == ep]
    avg_wait = (ep_df['we_waiting_time'].mean() + ep_df['ns_waiting_time'].mean()) / 2
    max_queue = max(ep_df['we_queue'].max(), ep_df['ns_queue'].max())
    
    # In RL, is it cumulative or per step?
    # Let's see if the column is cumulative or per step.
    # We can just sum it if it's per step, or max if cumulative.
    throughput_list.append(ep_df['completed_vehicles'].sum())
    avg_wait_list.append(avg_wait)
    max_queue_list.append(max_queue)

print(f"{'Frozen RL Agent':<20} | {np.mean(avg_wait_list):<12.2f} | {np.mean(max_queue_list):<15.0f} | {np.mean(throughput_list):<22.0f}")
