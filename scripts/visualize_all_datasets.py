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
        
        # Parse volume and balance
        match_vol = re.search(r'cars_(\d+)total', basename)
        if not match_vol:
            continue
        vol = int(match_vol.group(1))
        
        balance = "Asymmetric" if "unbalanced" in basename else "Symmetric"
        # Create a clean sorting string and display string
        scenario = f"{vol:04d}-{balance}"
        
        # Parse controller
        if "metrics_agent" in basename:
            controller = "Q-Agent"
        else:
            match_dur = re.search(r'dur_(\d+s)', basename)
            if match_dur:
                controller = f"Fixed-{match_dur.group(1)}"
            else:
                continue
                
        df = pd.read_csv(f)
        if df.empty: continue
        
        parsed_files.append(f)
        
        # Compute step-level metrics mapping to the requested column names
        if 'Avg_Waiting_Time_West_East' in df.columns:
            df['waiting_time'] = df[['Avg_Waiting_Time_West_East', 'Avg_Waiting_Time_North_South']].mean(axis=1)
            df['queue_length'] = df[['Queue_West_East', 'Queue_North_South']].mean(axis=1)
            df['throughput'] = df['Throughput_Step'] if 'Throughput_Step' in df.columns else 0
            
            # Aggregate for the scenario charts
            avg_wait = df['waiting_time'].mean()
            avg_queue = df['queue_length'].mean()
            avg_throughput = df['throughput'].mean()
            
            display_scenario = f"{vol} {balance}"
            
            all_data_agg.append({
                "Scenario_Sort": scenario,
                "Scenario": display_scenario,
                "Volume": vol,
                "Balance": balance,
                "Controller": controller,
                "Avg_Wait": avg_wait,
                "Avg_Queue": avg_queue,
                "Throughput": avg_throughput
            })
            
            all_step_data.append(df[['waiting_time', 'queue_length', 'throughput']])

    # Combine all step data to find true global min/max bounds dynamically
    if all_step_data:
        master_df = pd.concat(all_step_data, ignore_index=True)
        W_min, W_max = master_df['waiting_time'].min(), master_df['waiting_time'].max()
        Q_min, Q_max = master_df['queue_length'].min(), master_df['queue_length'].max()
        T_min, T_max = master_df['throughput'].min(), master_df['throughput'].max()
    else:
        W_min, W_max = 0, 327
        Q_min, Q_max = 0, 9
        T_min, T_max = 0, 1

    # To calculate theoretical mean step reward across all scenarios:
    def calc_reward(W, Q, T, w_W=0.5, w_Q=0.2, w_T=0.3, Ps=2.0):
        # We use dynamic global bounds
        W_q = np.maximum(0, 1.0 - (W / W_max)) if W_max > 0 else 0
        Q_q = np.maximum(0, 1.0 - (Q / Q_max)) if Q_max > 0 else 0
        T_q = T / max(1e-5, T_max)
        
        reward = w_W * W_q + w_T * T_q + w_Q * Q_q
        penalty = np.where(W > 100, Ps, 0)
        return reward - penalty

    # Now add theoretical step reward to aggregated data
    df_agg = pd.DataFrame(all_data_agg)
    # Sort by scenario properly
    df_agg.sort_values(by=["Scenario_Sort", "Controller"], inplace=True)
    df_agg['Mean_Reward'] = calc_reward(df_agg['Avg_Wait'], df_agg['Avg_Queue'], df_agg['Throughput'])
    
    # Generate Chart Sets A, B, C, D separately
    palette = {"Fixed-10s": "tab:blue", "Fixed-20s": "tab:orange", "Fixed-30s": "tab:green", "Fixed-45s": "tab:red", "Q-Agent": "black"}
    
    # Set A: Wait
    plt.figure(figsize=(16, 6), dpi=300)
    sns.barplot(data=df_agg, x="Scenario", y="Avg_Wait", hue="Controller", palette=palette)
    plt.title("Chart Set A: Average Waiting Time Across All Scenarios")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/chart_set_A_waiting_time.png")
    plt.close()
    
    # Set B: Queue
    plt.figure(figsize=(16, 6), dpi=300)
    sns.barplot(data=df_agg, x="Scenario", y="Avg_Queue", hue="Controller", palette=palette)
    plt.title("Chart Set B: Average Queue Length Across All Scenarios")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/chart_set_B_queue_length.png")
    plt.close()
    
    # Set C: Throughput
    plt.figure(figsize=(16, 6), dpi=300)
    sns.barplot(data=df_agg, x="Scenario", y="Throughput", hue="Controller", palette=palette)
    plt.title("Chart Set C: Throughput Rate Across All Scenarios")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/chart_set_C_throughput.png")
    plt.close()
    
    # Set D: Reward
    plt.figure(figsize=(16, 6), dpi=300)
    sns.barplot(data=df_agg, x="Scenario", y="Mean_Reward", hue="Controller", palette=palette)
    plt.title("Chart Set D: Mean Step Reward Across All Scenarios")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/chart_set_D_mean_reward.png")
    plt.close()
    
    # Dynamic Reward Parameter Decomposition
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)
    
    W_vals = np.linspace(W_min, W_max, 500)
    R_vs_W = calc_reward(W_vals, Q=Q_max/2, T=T_max/2)
    axes[0].plot(W_vals, R_vs_W, lw=2, color='darkblue')
    if W_max > 100:
        axes[0].axvline(100, color='red', linestyle='--', label='Starvation Threshold (W=100s)')
    axes[0].set_title("Reward vs Raw Waiting Time (W)")
    axes[0].set_xlabel(f"Waiting Time W ({W_min:.1f} to {W_max:.1f}s)")
    axes[0].set_ylabel("Total Reward R")
    if W_max > 100:
        axes[0].legend()
    axes[0].grid(True)
    
    Q_vals = np.linspace(Q_min, Q_max, 100)
    R_vs_Q = calc_reward(W=min(20, W_max), Q=Q_vals, T=T_max/2)
    axes[1].plot(Q_vals, R_vs_Q, lw=2, color='darkgreen')
    axes[1].set_title("Reward vs Raw Queue Length (Q)")
    axes[1].set_xlabel(f"Queue Length Q ({Q_min:.1f} to {Q_max:.1f} cars)")
    axes[1].set_ylabel("Total Reward R")
    axes[1].grid(True)
    
    T_vals = np.linspace(T_min, T_max, 100)
    R_vs_T = calc_reward(W=min(20, W_max), Q=Q_max/2, T=T_vals)
    axes[2].plot(T_vals, R_vs_T, lw=2, color='purple')
    axes[2].set_title("Reward vs Throughput Rate (T)")
    axes[2].set_xlabel(f"Throughput Rate T ({T_min:.1f} to {T_max:.1f} veh/step)")
    axes[2].set_ylabel("Total Reward R")
    axes[2].grid(True)
    
    plt.tight_layout()
    plt.savefig(f"{out_dir}/dynamic_reward_decomposition.png")
    plt.close()
    
    print("\nParsed CSV Files:")
    for pf in parsed_files:
        print(f" - {pf}")
    print(f"\nExtracted Dynamic Bounds: W[{W_min:.1f}, {W_max:.1f}], Q[{Q_min:.1f}, {Q_max:.1f}], T[{T_min:.1f}, {T_max:.1f}]")
    print("\nConfirmed Plots Generated:")
    print(f" - {out_dir}/chart_set_A_waiting_time.png")
    print(f" - {out_dir}/chart_set_B_queue_length.png")
    print(f" - {out_dir}/chart_set_C_throughput.png")
    print(f" - {out_dir}/chart_set_D_mean_reward.png")
    print(f" - {out_dir}/dynamic_reward_decomposition.png")

if __name__ == "__main__":
    main()
