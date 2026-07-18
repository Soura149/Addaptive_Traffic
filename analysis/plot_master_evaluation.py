import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    # 1. Read the compiled data
    df = pd.read_csv('sumofiles/compiled_agent_metrics.csv')
    
    # Extract data for plotting
    tiers = df['Car Tier'].astype(str).tolist()
    we_queues = df['Max WE Queue'].tolist()
    ns_queues = df['Max NS Queue'].tolist()
    mean_wait = df['Mean Waiting Time'].tolist()

    x = np.arange(len(tiers))  # the label locations
    width = 0.35  # the width of the bars

    # Create the figure and layout (1 row, 2 columns)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # ==========================================
    # LEFT PANEL (AXIS 1): Spatial Queue Cap
    # ==========================================
    rects1 = ax1.bar(x - width/2, we_queues, width, label='Max WE Queue', color='steelblue')
    rects2 = ax1.bar(x + width/2, ns_queues, width, label='Max NS Queue', color='#ff7f0e')

    # Formatting and labels
    ax1.set_xlabel('Traffic Volume Tiers (Total Cars)', fontsize=12)
    ax1.set_ylabel('Maximum Queue Length (Vehicles)', fontsize=12)
    ax1.set_title('A: Spatial Queue Cap (3:1 Flow Imbalance)', fontsize=14, fontweight='bold', loc='left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(tiers, fontsize=11)
    ax1.legend(fontsize=11)
    
    # Styling and limits
    ax1.set_ylim(0, max(max(we_queues), max(ns_queues)) + 2)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.yaxis.grid(True, linestyle='--', alpha=0.7)

    # Bar annotations
    def autolabel_bars(rects):
        for rect in rects:
            height = rect.get_height()
            ax1.annotate(f'{int(height)}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),  # 4 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    autolabel_bars(rects1)
    autolabel_bars(rects2)

    # ==========================================
    # RIGHT PANEL (AXIS 2): Systemic Latency Scaling
    # ==========================================
    ax2.plot(tiers, mean_wait, color='crimson', marker='o', markersize=8, linewidth=2, label='Avg Waiting Time')

    # Formatting and labels
    ax2.set_xlabel('Traffic Volume Tiers (Total Cars)', fontsize=12)
    ax2.set_ylabel('Average Waiting Time (Seconds)', fontsize=12)
    ax2.set_title('B: Systemic Latency Scaling (Delay Plateau)', fontsize=14, fontweight='bold', loc='left')
    ax2.set_xticks(range(len(tiers)))
    ax2.set_xticklabels(tiers, fontsize=11)
    
    # Styling and limits
    ax2.set_ylim(0, max(mean_wait) * 1.15)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    # Line annotations
    for i, wait_time in enumerate(mean_wait):
        ax2.annotate(f'{wait_time:.2f}',
                    xy=(i, wait_time),
                    xytext=(0, 10),  # 10 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=12, fontweight='bold', color='black')

    # Ensure clean spacing between subplots
    fig.tight_layout(pad=3.0)

    # 5. Output file
    output_filename = 'agent_master_evaluation.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Success: Master graph saved cleanly to {output_filename}")

if __name__ == "__main__":
    main()
