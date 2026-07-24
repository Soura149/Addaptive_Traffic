import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re

def main():
    sns.set_theme(style="whitegrid")
    out_dir = "outputs/visualizations"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Parsing all CSV files in collected_data/...")
    
    csv_files = glob.glob("collected_data/**/*.csv", recursive=True)
    
    all_data_agg = []
    parsed_files = []
    all_step_data = []
    
    for f in csv_files:
        basename = os.path.basename(f)
        
        match_vol = re.search(r'cars_(\d+)total', basename)
        if not match_vol: continue
        vol = int(match_vol.group(1))
        balance = "Asymmetric" if "unbalanced" in basename else "Symmetric"
        scenario = f"{vol:04d}-{balance}"
        
        if "metrics_agent" in basename:
            controller = "Q-Agent"
        else:
            match_dur = re.search(r'dur_(\d+s)', basename)
            if match_dur: controller = f"Fixed-{match_dur.group(1)}"
            else: continue
                
        df = pd.read_csv(f)
        if df.empty: continue
        
        parsed_files.append(f)
        
        if 'Avg_Waiting_Time_West_East' in df.columns:
            df['waiting_time'] = df[['Avg_Waiting_Time_West_East', 'Avg_Waiting_Time_North_South']].mean(axis=1)
            df['queue_length'] = df[['Queue_West_East', 'Queue_North_South']].mean(axis=1)
            df['throughput'] = df['Throughput_Step'] if 'Throughput_Step' in df.columns else 0
            
            avg_wait = df['waiting_time'].mean()
            avg_queue = df['queue_length'].mean()
            avg_throughput = df['throughput'].mean()
            
            all_data_agg.append({
                "Scenario_Sort": scenario,
                "Scenario": f"{vol} {balance}",
                "Volume": vol,
                "Balance": balance,
                "Controller": controller,
                "Avg_Wait": avg_wait,
                "Avg_Queue": avg_queue,
                "Throughput": avg_throughput
            })
            all_step_data.append(df[['waiting_time', 'queue_length', 'throughput']])

    if all_step_data:
        master_df = pd.concat(all_step_data, ignore_index=True)
        W_min, W_max = master_df['waiting_time'].min(), master_df['waiting_time'].max()
        Q_min, Q_max = master_df['queue_length'].min(), master_df['queue_length'].max()
        T_min, T_max = master_df['throughput'].min(), master_df['throughput'].max()
        W_mean, Q_mean, T_mean = master_df['waiting_time'].mean(), master_df['queue_length'].mean(), master_df['throughput'].mean()
    else:
        W_min, W_max, W_mean = 0, 327, 20
        Q_min, Q_max, Q_mean = 0, 9, 3
        T_min, T_max, T_mean = 0, 1, 0.5
        
    # We extend W_max to > 100 to explicitly visualize the starvation cliff if the raw max doesn't reach it.
    plot_W_max = max(W_max, 110.0)

    def calc_reward(W, Q, T, w_W=0.3, w_Q=0.2, w_T=0.5, Ps=2.0):
        # We use dynamic global max for normalization as extracted from raw data
        norm_W_max = W_max if W_max > 0 else 1.0
        norm_Q_max = Q_max if Q_max > 0 else 1.0
        norm_T_max = T_max if T_max > 0 else 1.0
        
        W_q = np.maximum(0, 1.0 - (W / norm_W_max))
        Q_q = np.maximum(0, 1.0 - (Q / norm_Q_max))
        T_q = T / norm_T_max
        
        reward = w_W * W_q + w_T * T_q + w_Q * Q_q
        penalty = np.where(W > 100, Ps, 0)
        return reward - penalty

    # Part 1: Mean Step Reward Comparative Benchmark
    df_agg = pd.DataFrame(all_data_agg)
    df_agg.sort_values(by=["Scenario_Sort", "Controller"], inplace=True)
    df_agg['Mean_Reward'] = calc_reward(df_agg['Avg_Wait'], df_agg['Avg_Queue'], df_agg['Throughput'])
    
    palette = {"Fixed-10s": "tab:blue", "Fixed-20s": "tab:orange", "Fixed-30s": "tab:green", "Fixed-45s": "tab:red", "Q-Agent": "black"}
    
    plt.figure(figsize=(16, 6), dpi=300)
    sns.barplot(data=df_agg, x="Scenario", y="Mean_Reward", hue="Controller", palette=palette)
    plt.title("Mean Step Reward Comparisons Across Scenarios")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/mean_step_reward_benchmark.png")
    plt.close()

    # Part 2: Multi-Parameter Reward Combination Matrices
    
    # Plot 1: 2D Heatmap (W x Q) at T_mean
    W_grid, Q_grid = np.meshgrid(np.linspace(W_min, plot_W_max, 200), np.linspace(Q_min, Q_max, 200))
    R_grid_1 = calc_reward(W_grid, Q_grid, T_mean)
    
    plt.figure(figsize=(10, 8), dpi=300)
    # Using contourf to display heatmap
    c = plt.contourf(W_grid, Q_grid, R_grid_1, levels=50, cmap='viridis')
    plt.colorbar(c, label='Total Reward R')
    plt.axvline(100, color='red', linestyle='--', linewidth=2, label='Starvation Cliff (>100s)')
    plt.title(f"Reward Heatmap: Waiting Time vs Queue Length (T={T_mean:.2f})")
    plt.xlabel(f"Raw Waiting Time W (s)")
    plt.ylabel("Raw Queue Length Q (cars)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{out_dir}/heatmap_W_vs_Q.png")
    plt.close()

    # Plot 2: 2D Heatmap (W x T) at Q_mean
    W_grid2, T_grid = np.meshgrid(np.linspace(W_min, plot_W_max, 200), np.linspace(T_min, T_max, 200))
    R_grid_2 = calc_reward(W_grid2, Q_mean, T_grid)
    
    plt.figure(figsize=(10, 8), dpi=300)
    c2 = plt.contourf(W_grid2, T_grid, R_grid_2, levels=50, cmap='plasma')
    plt.colorbar(c2, label='Total Reward R')
    plt.axvline(100, color='red', linestyle='--', linewidth=2, label='Starvation Cliff (>100s)')
    plt.title(f"Reward Heatmap: Waiting Time vs Throughput Rate (Q={Q_mean:.2f})")
    plt.xlabel(f"Raw Waiting Time W (s)")
    plt.ylabel("Raw Throughput Rate T (veh/step)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{out_dir}/heatmap_W_vs_T.png")
    plt.close()
    
    # Plot 3: Parameter Priority Shift Comparisons (Sensitivity Analysis)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)
    
    W_vals = np.linspace(W_min, plot_W_max, 500)
    
    # 3.1: Default System
    R_default = calc_reward(W_vals, Q_mean, T_mean, w_W=0.3, w_Q=0.2, w_T=0.5)
    axes[0].plot(W_vals, R_default, lw=2, color='blue')
    axes[0].axvline(100, color='red', linestyle='--', label='Starvation Cliff')
    axes[0].set_title("Default (w_W=0.3, w_T=0.5, w_Q=0.2)")
    axes[0].set_xlabel("Waiting Time W (s)")
    axes[0].set_ylabel("Reward R")
    axes[0].grid(True)
    axes[0].legend()
    
    # 3.2: Queue-Prioritized
    R_queue = calc_reward(W_vals, Q_mean, T_mean, w_W=0.2, w_T=0.2, w_Q=0.6)
    axes[1].plot(W_vals, R_queue, lw=2, color='green')
    axes[1].axvline(100, color='red', linestyle='--', label='Starvation Cliff')
    axes[1].set_title("Queue-Prioritized (w_W=0.2, w_T=0.2, w_Q=0.6)")
    axes[1].set_xlabel("Waiting Time W (s)")
    axes[1].grid(True)
    axes[1].legend()
    
    # 3.3: Throughput-Prioritized
    R_thru = calc_reward(W_vals, Q_mean, T_mean, w_W=0.2, w_T=0.6, w_Q=0.2)
    axes[2].plot(W_vals, R_thru, lw=2, color='purple')
    axes[2].axvline(100, color='red', linestyle='--', label='Starvation Cliff')
    axes[2].set_title("Throughput-Prioritized (w_W=0.2, w_T=0.6, w_Q=0.2)")
    axes[2].set_xlabel("Waiting Time W (s)")
    axes[2].grid(True)
    axes[2].legend()
    
    plt.tight_layout()
    plt.savefig(f"{out_dir}/priority_shift_comparisons.png")
    plt.close()
    
    print("\nSummary: Data extraction successful.")
    print(f"Extracted dynamic true bounds from {len(parsed_files)} files.")
    print(f"Global W_max: {W_max:.1f}, Q_max: {Q_max:.1f}, T_max: {T_max:.1f}")
    print("\nGenerated Figures:")
    print(f" - {out_dir}/mean_step_reward_benchmark.png")
    print(f" - {out_dir}/heatmap_W_vs_Q.png")
    print(f" - {out_dir}/heatmap_W_vs_T.png")
    print(f" - {out_dir}/priority_shift_comparisons.png")

if __name__ == "__main__":
    main()
