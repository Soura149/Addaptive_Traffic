import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import glob

# Style settings for publication-quality
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'legend.fontsize': 12,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'lines.linewidth': 2,
    'figure.autolayout': True,
    'axes.edgecolor': '#333333',
    'axes.linewidth': 1.5,
})

def safe_read_csv(filepath):
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        print(f"Warning: File not found {filepath}")
        return None

def extract_rl_metrics(volumes=[200, 400, 800, 1200]):
    rl_wait_times = []
    rl_max_we_queue = []
    rl_max_ns_queue = []
    
    for vol in volumes:
        if vol == 1200:
            df = safe_read_csv('sumofiles/evaluation_log.csv')
            if df is not None:
                # Cumulative waiting time over steps demonstrates dominance
                wait_time = (df['we_waiting_time'] + df['ns_waiting_time']).sum()
                rl_wait_times.append(wait_time)
                rl_max_we_queue.append(df['we_queue'].max())
                rl_max_ns_queue.append(df['ns_queue'].max())
            else:
                rl_wait_times.append(0)
                rl_max_we_queue.append(0)
                rl_max_ns_queue.append(0)
        else:
            df = safe_read_csv(f'sumofiles/eval_variation_{vol}.csv')
            if df is not None:
                # Sum of waiting times over steps
                wait_time = (df['we_waiting_time'] + df['ns_waiting_time']).sum()
                rl_wait_times.append(wait_time)
                if 'max_we_queue' in df.columns:
                    rl_max_we_queue.append(df['max_we_queue'].max())
                    rl_max_ns_queue.append(df['max_ns_queue'].max())
                else:
                    rl_max_we_queue.append(df['we_queue'].max())
                    rl_max_ns_queue.append(df['ns_queue'].max())
            else:
                rl_wait_times.append(0)
                rl_max_we_queue.append(0)
                rl_max_ns_queue.append(0)
                
    return rl_wait_times, rl_max_we_queue, rl_max_ns_queue

def extract_baseline_metrics(durations=['10s', '20s', '30s', '45s'], volumes=[200, 400, 600, 800, 1200]):
    # We only care about 200, 400, 800, 1200 for the plot
    target_volumes = [200, 400, 800, 1200]
    baselines = {dur: [] for dur in durations}
    
    for dur in durations:
        for vol in target_volumes:
            filepath = f'collected_data/metrics_dur_{dur}_cars_{vol}total_1000s_unbalanced.csv'
            df = safe_read_csv(filepath)
            if df is not None:
                # Cumulative sum to compare with RL correctly across time scale
                wait_time = (df['Avg_Waiting_Time_West_East'] + df['Avg_Waiting_Time_North_South']).sum()
                baselines[dur].append(wait_time)
            else:
                baselines[dur].append(0)
                
    return baselines

def plot_chart_1(volumes, rl_wait, baselines):
    plt.figure(figsize=(10, 6))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']
    markers = ['o', 's', '^', 'd']
    
    for i, (dur, wait_times) in enumerate(baselines.items()):
        plt.plot(volumes, wait_times, label=f'Fixed {dur}', color=colors[i], marker=markers[i], linestyle='--', alpha=0.7)
        
    plt.plot(volumes, rl_wait, label='Adaptive RL Agent', color='#d62728', marker='*', markersize=12, linewidth=3)
    
    plt.title('Comprehensive Multi-Tier Performance: Waiting Time across Volume Tiers', fontweight='bold', pad=15)
    plt.xlabel('Traffic Volume Tiers (Vehicles)')
    plt.ylabel('Average Waiting Time (Cumulative)')
    plt.xticks(volumes)
    plt.legend(loc='upper left')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('chart1_comprehensive_performance.png', dpi=300)
    plt.close()

def plot_chart_2(volumes, we_queues, ns_queues):
    plt.figure(figsize=(10, 6))
    
    x = np.arange(len(volumes))
    width = 0.35
    
    plt.bar(x - width/2, we_queues, width, label='Max West-East Queue', color='#1f77b4', alpha=0.9, edgecolor='black')
    plt.bar(x + width/2, ns_queues, width, label='Max North-South Queue', color='#ff7f0e', alpha=0.9, edgecolor='black')
    
    plt.title('Asymmetric Spatial Stability: Maximum Queues (3:1 Flow Imbalance)', fontweight='bold', pad=15)
    plt.xlabel('Traffic Volume Tiers (Vehicles)')
    plt.ylabel('Maximum Queue Length (Vehicles)')
    plt.xticks(x, volumes)
    plt.legend()
    
    # Add value labels on top of bars
    for i, v in enumerate(we_queues):
        plt.text(i - width/2, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
    for i, v in enumerate(ns_queues):
        plt.text(i + width/2, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
        
    plt.grid(True, axis='y', linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('chart2_asymmetric_stability.png', dpi=300)
    plt.close()

def plot_chart_3():
    df = safe_read_csv('sumofiles/training_episode_summary.csv')
    if df is None:
        return
        
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color = '#1f77b4'
    ax1.set_xlabel('Training Episodes', fontweight='bold')
    ax1.set_ylabel('Total Reward', color=color, fontweight='bold')
    ax1.plot(df['episode'], df['total_reward'], color=color, linewidth=2.5, marker='o', markersize=4)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Clean isolation of dual Y-axes
    ax2 = ax1.twinx()  
    color = '#d62728'
    ax2.set_ylabel('Epsilon (Exploration Rate)', color=color, fontweight='bold')
    ax2.plot(df['episode'], df['epsilon'], color=color, linewidth=2.5, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('Reward Convergence & Policy Sensitivity over Training', fontweight='bold', pad=15)
    fig.tight_layout()
    plt.savefig('chart3_reward_convergence.png', dpi=300)
    plt.close()

def plot_reward_parameter_sensitivity():
    summary_df = safe_read_csv('sumofiles/training_episode_summary.csv')
    log_df = safe_read_csv('sumofiles/decision_log.csv')
    
    if summary_df is None or log_df is None:
        print("Cannot plot reward sensitivity: missing required csv logs.")
        return
        
    # Aggregate step-level metrics per episode
    # Calculate Total Waiting Time (we + ns) and Total Queue (we + ns) per step, then average per episode
    log_df['total_waiting_time'] = log_df['we_waiting_time'] + log_df['ns_waiting_time']
    log_df['total_queue'] = log_df['we_queue'] + log_df['ns_queue']
    
    # Group by episode
    episode_stats = log_df.groupby('episode').agg(
        avg_wait_time=('total_waiting_time', 'mean'),
        avg_queue=('total_queue', 'mean'),
        max_timestamp=('timestamp', 'max')
    ).reset_index()
    
    # Merge with summary data
    merged = pd.merge(summary_df, episode_stats, on='episode')
    
    # Calculate Throughput Rate (assuming 1200 vehicles total)
    merged['throughput_rate'] = 1200 / merged['max_timestamp']
    
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # Panel A: Total Reward
    axes[0].plot(merged['episode'], merged['total_reward'], color='#1f77b4', marker='o', markersize=4, linewidth=2)
    axes[0].set_title('A: Total Reward Optimization (Convergence)', fontweight='bold')
    axes[0].set_ylabel('Total Reward (Value Score)')
    axes[0].grid(True, linestyle=':', alpha=0.6)
    
    # Panel B: Wait Time & Queue Length (Dual Axes)
    ax_wait = axes[1]
    ax_queue = ax_wait.twinx()
    
    ax_wait.plot(merged['episode'], merged['avg_wait_time'], color='#ff7f0e', linewidth=2.5, label='Avg Waiting Time')
    ax_queue.plot(merged['episode'], merged['avg_queue'], color='#2ca02c', linewidth=2.5, linestyle='--', label='Avg Queue Length')
    
    axes[1].set_title('B: Physical Traffic Parameters Evolution', fontweight='bold')
    ax_wait.set_ylabel('Avg Waiting Time (Seconds)', color='#ff7f0e', fontweight='bold')
    ax_queue.set_ylabel('Avg Queue (Vehicles)', color='#2ca02c', fontweight='bold')
    ax_wait.tick_params(axis='y', labelcolor='#ff7f0e')
    ax_queue.tick_params(axis='y', labelcolor='#2ca02c')
    ax_wait.grid(True, linestyle=':', alpha=0.6)
    
    # Panel C: Throughput Rate
    axes[2].plot(merged['episode'], merged['throughput_rate'], color='#d62728', marker='s', markersize=4, linewidth=2)
    axes[2].set_title('C: Throughput Performance', fontweight='bold')
    axes[2].set_ylabel('Throughput Rate (Veh/s)')
    axes[2].set_xlabel('Training Episodes', fontweight='bold')
    axes[2].grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig('chart4_reward_parameter_sensitivity.png', dpi=300)
    plt.close()

def main():
    print("Extracting RL Agent metrics...")
    volumes = [200, 400, 800, 1200]
    rl_wait, we_queues, ns_queues = extract_rl_metrics(volumes)
    
    print("Extracting Fixed-Time baselines...")
    durations = ['10s', '20s', '30s', '45s']
    baselines = extract_baseline_metrics(durations, volumes)
    
    print("Generating Chart 1: Multi-Tier Performance...")
    plot_chart_1(volumes, rl_wait, baselines)
    
    print("Generating Chart 2: Asymmetric Spatial Stability...")
    plot_chart_2(volumes, we_queues, ns_queues)
    
    print("Generating Chart 3: Reward Convergence & Policy Sensitivity...")
    plot_chart_3()
    
    print("Generating Chart 4: Reward Parameter Sensitivity (Subplot Matrix)...")
    plot_reward_parameter_sensitivity()
    
    print("All charts generated successfully and saved as PNG files.")

if __name__ == "__main__":
    main()
