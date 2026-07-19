import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "new_experiment_analytics")

def ensure_isolated_directory(dir_name=DATA_DIR):
    """Creates an isolated directory for the new outputs."""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name

def plot_learning_convergence(output_dir):
    """Chart 1: Learning Convergence Curve with Dual-Axis"""
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, "training_episode_summary.csv"))
    except FileNotFoundError:
        print("training_episode_summary.csv not found.")
        return
        
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color = 'tab:blue'
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Total Reward', color=color)
    ax1.plot(df['episode'], df['total_reward'], color=color, marker='o', linestyle='-', label='Total Reward')
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  
    color = 'tab:red'
    ax2.set_ylabel('Epsilon', color=color)  
    ax2.plot(df['episode'], df['epsilon'], color=color, linestyle='--', label='Epsilon Decay')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title('Learning Convergence Curve')
    fig.tight_layout()  
    
    out_path = os.path.join(output_dir, "learning_convergence.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {out_path}")

def plot_baseline_comparison(output_dir):
    """Chart 2: Three-Panel Baseline Performance Matrix"""
    data = []
    
    # RL Agent
    try:
        rl_df = pd.read_csv(os.path.join(DATA_DIR, "evaluation_log.csv"))
        rl_delay = (rl_df['we_waiting_time'] + rl_df['ns_waiting_time']).mean()
        rl_queue = (rl_df['we_queue'] + rl_df['ns_queue']).mean()
        if 'completed_vehicles' in rl_df.columns:
            rl_throughput = rl_df.groupby('episode')['completed_vehicles'].sum().mean()
        else:
            rl_throughput = 0
            
        data.append({
            'Agent': 'RL Agent',
            'Avg Delay': rl_delay,
            'Avg Queue': rl_queue,
            'Throughput': rl_throughput
        })
    except Exception as e:
        print(f"Could not process evaluation_log.csv: {e}")
        
    # Baselines
    for dur in [10, 20, 30, 45]:
        b_file = os.path.join(DATA_DIR, f"baseline_{dur}s.csv")
        try:
            b_df = pd.read_csv(b_file)
            b_delay = (b_df['we_waiting_time'] + b_df['ns_waiting_time']).mean()
            b_queue = (b_df['we_queue'] + b_df['ns_queue']).mean()
            b_throughput = b_df['completed_vehicles'].sum()
            
            data.append({
                'Agent': f'Fixed {dur}s',
                'Avg Delay': b_delay,
                'Avg Queue': b_queue,
                'Throughput': b_throughput
            })
        except Exception as e:
            print(f"Could not process {b_file}: {e}")
            
    if not data:
        print("No evaluation or baseline data found.")
        return
        
    df_metrics = pd.DataFrame(data)
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Avg Delay
    sns.barplot(x='Agent', y='Avg Delay', hue='Agent', data=df_metrics, ax=axes[0], palette="viridis", legend=False)
    axes[0].set_title("Average System Delay (Waiting Time)")
    axes[0].set_ylabel("Time (s)")
    axes[0].tick_params(axis='x', rotation=45)
    
    # Spatial Queue
    sns.barplot(x='Agent', y='Avg Queue', hue='Agent', data=df_metrics, ax=axes[1], palette="magma", legend=False)
    axes[1].set_title("Spatial Queue Length Accumulation")
    axes[1].set_ylabel("Vehicles")
    axes[1].tick_params(axis='x', rotation=45)
    
    # Throughput
    sns.barplot(x='Agent', y='Throughput', hue='Agent', data=df_metrics, ax=axes[2], palette="crest", legend=False)
    axes[2].set_title("Cumulative Completed Throughput")
    axes[2].set_ylabel("Vehicles Processed")
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    out_path = os.path.join(output_dir, "baseline_performance_matrix.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {out_path}")

def plot_reward_sensitivity(output_dir):
    """Chart 3: Reward Parameter Sensitivity Analysis"""
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, "decision_log.csv"))
    except FileNotFoundError:
        print("decision_log.csv not found.")
        return
        
    plt.figure(figsize=(10, 8))
    
    scatter = plt.scatter(
        df['we_waiting_time'], 
        df['ns_waiting_time'], 
        c=df['reward'], 
        cmap='coolwarm', 
        alpha=0.6,
        edgecolors='w',
        linewidth=0.5
    )
    
    plt.colorbar(scatter, label='Absolute Reward')
    plt.xlabel('West-East Waiting Time (s)')
    plt.ylabel('North-South Waiting Time (s)')
    plt.title('Reward Parameter Sensitivity: WE vs NS Delay Trade-off')
    
    if not df.empty:
        max_val = max(df['we_waiting_time'].max(), df['ns_waiting_time'].max())
        if pd.notna(max_val):
            plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label='Symmetric Delay Line')
            plt.legend()
    
    plt.tight_layout()
    out_path = os.path.join(output_dir, "reward_parameter_sensitivity.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved {out_path}")

if __name__ == "__main__":
    output_directory = ensure_isolated_directory()
    print(f"Initialized output directory: {output_directory}")
    
    plot_learning_convergence(output_directory)
    plot_baseline_comparison(output_directory)
    plot_reward_sensitivity(output_directory)
    print("All visualizations generated successfully.")
