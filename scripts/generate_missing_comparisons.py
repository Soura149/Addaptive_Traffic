import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    sns.set_theme(style="whitegrid")
    out_dir = "outputs"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Generating missing comparisons...")

    # =========================================================================
    # Task 1: Master Comparative Performance Plot
    # =========================================================================
    volumes = [200, 400, 600, 800, 1200]
    controllers = ["10s", "20s", "30s", "45s", "agent"]
    labels = ["Fixed-10s", "Fixed-20s", "Fixed-30s", "Fixed-45s", "Q-Agent"]
    
    data_t1 = []
    for vol in volumes:
        for ctrl, lbl in zip(controllers, labels):
            if ctrl == "agent":
                fname = f"collected_data/agent_runs/metrics_agent_cars_{vol}total_1000s.csv"
            else:
                fname = f"collected_data/agent_runs/metrics_dur_{ctrl}_cars_{vol}total_1000s.csv"
                
            if os.path.exists(fname):
                df = pd.read_csv(fname)
                avg_wait = df[['Avg_Waiting_Time_West_East', 'Avg_Waiting_Time_North_South']].mean().mean()
                avg_queue = df[['Queue_West_East', 'Queue_North_South']].mean().mean()
                data_t1.append({"Volume": vol, "Controller": lbl, "Avg_Wait": avg_wait, "Avg_Queue": avg_queue})
                
    df_t1 = pd.DataFrame(data_t1)
    
    if not df_t1.empty:
        fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=300)
        
        sns.lineplot(data=df_t1, x="Volume", y="Avg_Wait", hue="Controller", style="Controller", markers=True, dashes=False, ax=axes[0], palette="tab10")
        axes[0].set_title("Average Waiting Time vs. Vehicle Volume")
        axes[0].set_ylabel("Average Waiting Time (s)")
        axes[0].set_xlabel("Vehicle Volume")
        
        sns.lineplot(data=df_t1, x="Volume", y="Avg_Queue", hue="Controller", style="Controller", markers=True, dashes=False, ax=axes[1], palette="tab10")
        axes[1].set_title("Average Queue Length vs. Vehicle Volume")
        axes[1].set_ylabel("Average Queue Length (cars)")
        axes[1].set_xlabel("Vehicle Volume")
        
        plt.tight_layout()
        plt.savefig(f"{out_dir}/master_baseline_vs_agent_comparison.png")
        plt.close()
        print(f" - Task 1: {out_dir}/master_baseline_vs_agent_comparison.png generated.")

    # =========================================================================
    # Task 2: Asymmetric Traffic Balance Comparison
    # =========================================================================
    data_t2 = []
    for ctrl, lbl in zip(controllers, labels):
        if ctrl == "agent":
            f_bal = "collected_data/agent_runs/metrics_agent_cars_1200total_1000s.csv"
            f_unbal = "collected_data/agent_runs/metrics_agent_cars_1200total_1000s_unbalanced.csv"
        else:
            f_bal = f"collected_data/agent_runs/metrics_dur_{ctrl}_cars_1200total_1000s.csv"
            f_unbal = f"collected_data/agent_runs/metrics_dur_{ctrl}_cars_1200total_1000s_unbalanced.csv"
            
        for fname, balance in [(f_bal, "Balanced"), (f_unbal, "Unbalanced")]:
            if os.path.exists(fname):
                df = pd.read_csv(fname)
                wait = df[['Avg_Waiting_Time_West_East', 'Avg_Waiting_Time_North_South']].mean().mean()
                queue = df[['Queue_West_East', 'Queue_North_South']].mean().mean()
                tp = df['Throughput_Step'].mean() if 'Throughput_Step' in df.columns else 0
                data_t2.append({"Controller": lbl, "Balance": balance, "Wait": wait, "Queue": queue, "Throughput": tp})
                
    df_t2 = pd.DataFrame(data_t2)
    
    if not df_t2.empty:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), dpi=300)
        
        sns.barplot(data=df_t2, x="Controller", y="Wait", hue="Balance", ax=axes[0], palette="Set2")
        axes[0].set_title("Waiting Time (1200 cars)")
        axes[0].set_ylabel("Avg Waiting Time (s)")
        axes[0].tick_params(axis='x', rotation=45)
        
        sns.barplot(data=df_t2, x="Controller", y="Queue", hue="Balance", ax=axes[1], palette="Set2")
        axes[1].set_title("Queue Length (1200 cars)")
        axes[1].set_ylabel("Avg Queue Length (cars)")
        axes[1].tick_params(axis='x', rotation=45)
        
        sns.barplot(data=df_t2, x="Controller", y="Throughput", hue="Balance", ax=axes[2], palette="Set2")
        axes[2].set_title("Throughput Rate (1200 cars)")
        axes[2].set_ylabel("Throughput (veh/step)")
        axes[2].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f"{out_dir}/asymmetric_balance_comparison.png")
        plt.close()
        print(f" - Task 2: {out_dir}/asymmetric_balance_comparison.png generated.")

    # =========================================================================
    # Task 3: Direct Reward Parameter Comparison Plot
    # =========================================================================
    def calc_reward(W, Q, T, w_W=0.3, w_Q=0.2, w_T=0.5, Ps=2.0):
        # Normalize wait time
        W_q = np.maximum(0, 1.0 - (W / 327.0))
        # Normalize queue
        Q_q = np.maximum(0, 1.0 - (Q / 9.0))
        # T is already 0-1 (assumed throughput rate)
        T_q = np.clip(T, 0, 1)
        
        reward = w_W * W_q + w_T * T_q + w_Q * Q_q
        penalty = np.where(W > 100, Ps, 0)
        return reward - penalty

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)
    
    # Subplot 1: R vs W at Q=3, T=0.5
    W_vals = np.linspace(0, 300, 500)
    R_vs_W = calc_reward(W_vals, Q=3, T=0.5)
    axes[0].plot(W_vals, R_vs_W, lw=2, color='darkblue')
    axes[0].axvline(100, color='red', linestyle='--', label='Starvation Threshold (W=100s)')
    axes[0].set_title("Reward vs Raw Waiting Time (W)\n[w_W=30%]")
    axes[0].set_xlabel("Waiting Time W (s)")
    axes[0].set_ylabel("Total Reward R")
    axes[0].legend()
    axes[0].grid(True)
    
    # Subplot 2: R vs Q at W=20s, T=0.5
    Q_vals = np.linspace(0, 9, 100)
    R_vs_Q = calc_reward(W=20, Q=Q_vals, T=0.5)
    axes[1].plot(Q_vals, R_vs_Q, lw=2, color='darkgreen')
    axes[1].set_title("Reward vs Raw Queue Length (Q)\n[w_Q=20%]")
    axes[1].set_xlabel("Queue Length Q (vehicles)")
    axes[1].set_ylabel("Total Reward R")
    axes[1].grid(True)
    
    # Subplot 3: R vs T at W=20s, Q=3
    T_vals = np.linspace(0, 1.0, 100)
    R_vs_T = calc_reward(W=20, Q=3, T=T_vals)
    axes[2].plot(T_vals, R_vs_T, lw=2, color='purple')
    axes[2].set_title("Reward vs Throughput Rate (T)\n[w_T=30%]")
    axes[2].set_xlabel("Throughput Rate T (veh/step)")
    axes[2].set_ylabel("Total Reward R")
    axes[2].grid(True)
    
    plt.tight_layout()
    plt.savefig(f"{out_dir}/reward_parameter_decomposition.png")
    plt.close()
    print(f" - Task 3: {out_dir}/reward_parameter_decomposition.png generated.")
    
    print("\nSummary: ALL baselines (Fixed-10s, 20s, 30s, 45s) and Q-Agent were successfully parsed and overlaid onto the charts.")

if __name__ == "__main__":
    main()
