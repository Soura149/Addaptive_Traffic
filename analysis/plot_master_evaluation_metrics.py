import matplotlib.pyplot as plt
import numpy as np

def main():
    # Extracted data from console output
    tiers = ['200', '400', '800', '1200']
    mean_wait = [42.25, 100.53, 126.63, 131.71]
    max_we = [7, 7, 7, 7]
    max_ns = [0, 0, 0, 1]
    we_sd = [2.26, 1.87, 1.54, 1.05]
    ns_sd = [0.0, 0.0, 0.0, 0.13]

    # Create the figure with 3 rows, 1 column, shared X-axis
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 14), sharex=True)
    x = np.arange(len(tiers))
    width = 0.35

    # ==========================================
    # Panel A (Top): System Delay Scaling
    # ==========================================
    ax1.plot(x, mean_wait, color='crimson', marker='o', markersize=8, linewidth=2)
    ax1.set_ylabel('Avg Waiting Time (s)', fontsize=12, fontweight='bold')
    ax1.set_title('A: System Delay Scaling', fontsize=14, fontweight='bold', loc='left')
    ax1.set_ylim(0, max(mean_wait) * 1.2)
    
    # Polish styles
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    # Value annotations
    for i, val in enumerate(mean_wait):
        ax1.annotate(f'{val:.2f}', xy=(x[i], val), xytext=(0, 8), textcoords='offset points', ha='center', va='bottom', fontsize=11, fontweight='bold')


    # ==========================================
    # Panel B (Middle): Spatial Queue Caps
    # ==========================================
    rects1 = ax2.bar(x - width/2, max_we, width, label='Max WE Queue', color='steelblue')
    rects2 = ax2.bar(x + width/2, max_ns, width, label='Max NS Queue', color='#ff7f0e')
    
    ax2.set_ylabel('Max Queue Length (Vehicles)', fontsize=12, fontweight='bold')
    ax2.set_title('B: Spatial Queue Caps', fontsize=14, fontweight='bold', loc='left')
    ax2.set_ylim(0, max(max(max_we), max(max_ns)) + 2)
    
    # Polish styles
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(fontsize=11, loc='upper left')

    # Bar annotations
    def autolabel_int(rects, ax):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{int(height)}', xy=(rect.get_x() + rect.get_width() / 2, height), xytext=(0, 4), textcoords='offset points', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    autolabel_int(rects1, ax2)
    autolabel_int(rects2, ax2)


    # ==========================================
    # Panel C (Bottom): Queue Volatility & Stability (SD)
    # ==========================================
    # Using grouped bar chart for clear visual comparison alongside the Max queue chart
    rects3 = ax3.bar(x - width/2, we_sd, width, label='WE Queue SD', color='steelblue', alpha=0.75)
    rects4 = ax3.bar(x + width/2, ns_sd, width, label='NS Queue SD', color='#ff7f0e', alpha=0.75)
    
    ax3.set_ylabel('Queue Std Deviation (SD)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Traffic Volume Tiers (Total Cars)', fontsize=13, fontweight='bold')
    ax3.set_title('C: Queue Volatility Dynamics (Standard Deviation Decline)', fontsize=14, fontweight='bold', loc='left')
    
    ax3.set_xticks(x)
    ax3.set_xticklabels(tiers, fontsize=12)
    ax3.set_ylim(0, max(max(we_sd), max(ns_sd)) * 1.3)
    
    # Polish styles
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax3.legend(fontsize=11, loc='upper right')

    # Float annotations
    def autolabel_float(rects, ax):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height), xytext=(0, 4), textcoords='offset points', ha='center', va='bottom', fontsize=11, fontweight='bold')
            
    autolabel_float(rects3, ax3)
    autolabel_float(rects4, ax3)


    # Final Layout Tweaks
    fig.tight_layout(pad=2.0)
    output_filename = 'agent_comprehensive_evaluation.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Success: Master graph saved cleanly to {output_filename}")


if __name__ == "__main__":
    main()
