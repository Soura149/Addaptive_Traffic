import matplotlib.pyplot as plt

def main():
    # Verified dataset from the console output
    tiers = ['200', '400', '800', '1200']
    
    baseline_10s = [3.44, 3.44, 3.44, 3.33]
    baseline_20s = [5.64, 5.64, 5.64, 6.20]
    baseline_30s = [8.67, 8.67, 8.67, 9.46]
    baseline_45s = [13.64, 13.64, 13.64, 14.41]
    rl_agent = [11.2, 12.8, 14.1, 13.9]
    
    # Initialize the figure and axis
    fig, ax = plt.subplots(figsize=(11, 7))
    
    # Plot the 4 baselines using distinct styles but keeping them visually grouped (dashed lines)
    ax.plot(tiers, baseline_10s, label='Fixed 10s Baseline', color='tab:blue', linestyle='--', marker='s', linewidth=2, markersize=6)
    ax.plot(tiers, baseline_20s, label='Fixed 20s Baseline', color='tab:orange', linestyle='--', marker='^', linewidth=2, markersize=6)
    ax.plot(tiers, baseline_30s, label='Fixed 30s Baseline', color='tab:green', linestyle='--', marker='v', linewidth=2, markersize=6)
    ax.plot(tiers, baseline_45s, label='Fixed 45s Baseline', color='tab:purple', linestyle='--', marker='D', linewidth=2, markersize=6)
    
    # Plot the RL Agent prominently
    ax.plot(tiers, rl_agent, label='Adaptive RL Agent (Queue Capping)', color='crimson', linestyle='-', marker='o', linewidth=3, markersize=9)
    
    # Presentation Polish and Labels
    ax.set_xlabel('Traffic Volume Tiers (Total Cars)', fontsize=12, fontweight='bold')
    ax.set_ylabel('System Delay Metric (Seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Performance Comparison Matrix: Delay Profiles vs Flow Load', fontsize=15, fontweight='bold')
    
    # Grid lines matching previous charts
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    # Enhance legend
    ax.legend(fontsize=11, loc='upper left', frameon=True, framealpha=0.9, shadow=True)
    
    # Ensure layout fits perfectly
    fig.tight_layout()
    
    # Output file
    output_filename = 'performance_comparison_matrix.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Success: Master graph saved cleanly to {output_filename}")

if __name__ == "__main__":
    main()
