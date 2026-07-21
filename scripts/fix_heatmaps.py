import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    sns.set_theme(style="white")
    out_dir = "outputs"
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Physical Metric Bounds & Grid Resolution
    W_min, W_max = 0.0, 120.0
    Q_min, Q_max = 0.0, 9.0
    T_min, T_max = 0.0, 1.0
    grid_res = 200
    
    # Reward Function Calculation (using standardized maxes for normalization)
    def calc_reward(W, Q, T, w_W=0.5, w_Q=0.2, w_T=0.3, Ps=2.0):
        # We normalize W up to 327 and Q up to 9 to match original state formulations
        W_q = np.maximum(0, 1.0 - (W / 327.0))
        Q_q = np.maximum(0, 1.0 - (Q / 9.0))
        T_q = np.clip(T, 0, 1.0)
        
        reward = w_W * W_q + w_T * T_q + w_Q * Q_q
        penalty = np.where(W > 100, Ps, 0)
        return reward - penalty

    # =========================================================================
    # Figure 1: Smooth Heatmap - Waiting Time (W) vs. Queue Length (Q)
    # =========================================================================
    W_vals = np.linspace(W_min, W_max, grid_res)
    Q_vals = np.linspace(Q_min, Q_max, grid_res)
    W_grid, Q_grid = np.meshgrid(W_vals, Q_vals)
    
    # Fixed T = 0.35 veh/s
    T_fixed = 0.35
    R_grid_1 = calc_reward(W_grid, Q_grid, T_fixed)
    
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    # Using contourf with 100 levels for silky-smooth gradient
    c1 = ax.contourf(W_grid, Q_grid, R_grid_1, levels=100, cmap='viridis')
    cbar1 = fig.colorbar(c1, ax=ax, label='Reward R')
    
    # Add clean dashed red line at W = 100s
    ax.axvline(100, color='red', linestyle='--', linewidth=2, label='Starvation Penalty Cliff (Ps = 2.0)')
    
    ax.set_title(f"Smooth Heatmap: Waiting Time (W) vs Queue Length (Q)\n[Fixed Throughput T = {T_fixed} veh/s]")
    ax.set_xlabel("Waiting Time W (s)")
    ax.set_ylabel("Queue Length Q (vehicles)")
    ax.set_xlim(W_min, W_max)
    ax.set_ylim(Q_min, Q_max)
    ax.legend(loc='lower left')
    
    plt.tight_layout()
    plt.savefig(f"{out_dir}/reward_heatmap_wait_vs_queue_fixed.png")
    plt.close()
    
    # =========================================================================
    # Figure 2: Smooth Heatmap - Waiting Time (W) vs. Throughput Rate (T)
    # =========================================================================
    T_vals = np.linspace(T_min, T_max, grid_res)
    W_grid2, T_grid = np.meshgrid(W_vals, T_vals)
    
    # Fixed Q = 2.0 vehicles
    Q_fixed = 2.0
    R_grid_2 = calc_reward(W_grid2, Q_fixed, T_grid)
    
    fig2, ax2 = plt.subplots(figsize=(10, 8), dpi=300)
    c2 = ax2.contourf(W_grid2, T_grid, R_grid_2, levels=100, cmap='plasma')
    cbar2 = fig2.colorbar(c2, ax=ax2, label='Reward R')
    
    # Add clean dashed red line at W = 100s
    ax2.axvline(100, color='red', linestyle='--', linewidth=2, label='Starvation Penalty Cliff (Ps = 2.0)')
    
    ax2.set_title(f"Smooth Heatmap: Waiting Time (W) vs Throughput Rate (T)\n[Fixed Queue Length Q = {Q_fixed} cars]")
    ax2.set_xlabel("Waiting Time W (s)")
    ax2.set_ylabel("Throughput Rate T (veh/s)")
    ax2.set_xlim(W_min, W_max)
    ax2.set_ylim(T_min, T_max)
    ax2.legend(loc='lower left')
    
    plt.tight_layout()
    plt.savefig(f"{out_dir}/reward_heatmap_wait_vs_throughput_fixed.png")
    plt.close()

    print("Successfully generated fixed heatmaps:")
    print(f" - {out_dir}/reward_heatmap_wait_vs_queue_fixed.png")
    print(f" - {out_dir}/reward_heatmap_wait_vs_throughput_fixed.png")

if __name__ == "__main__":
    main()
