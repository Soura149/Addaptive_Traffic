import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    # 1. Read the compiled data
    df = pd.read_csv('sumofiles/compiled_agent_metrics.csv')
    
    # 2. Extract arrays for plotting
    tiers = df['Car Tier'].astype(str).tolist()
    we_queues = df['Max WE Queue'].tolist()
    ns_queues = df['Max NS Queue'].tolist()

    x = np.arange(len(tiers))  # the label locations
    width = 0.35  # the width of the bars

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(9, 6))

    # 3. Plot bars with requested colors (Steel Blue and Safety Orange)
    rects1 = ax.bar(x - width/2, we_queues, width, label='Max WE Queue', color='steelblue')
    rects2 = ax.bar(x + width/2, ns_queues, width, label='Max NS Queue', color='#ff7f0e')

    # Add text for labels, title, custom x-axis tick labels, etc.
    ax.set_xlabel('Traffic Volume Tiers (Total Cars)', fontsize=12)
    ax.set_ylabel('Maximum Queue Length (Vehicles)', fontsize=12)
    ax.set_title('Evaluation of Maximum Queue Lengths Across Traffic Volumes', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(tiers, fontsize=11)
    ax.legend(fontsize=11)
    
    # Set y-axis to be slightly larger than the max value for better text placement
    max_queue_val = max(max(we_queues), max(ns_queues))
    ax.set_ylim(0, max_queue_val + 2)
    
    # Optional styling for publication-grade
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)

    # 4. Attach a text label above each bar, displaying its integer height.
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{int(height)}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),  # 4 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=12, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()

    # 5. Output file
    output_filename = 'agent_evaluation_queues.png'
    plt.savefig(output_filename, dpi=300)
    print(f"Success: Graph saved cleanly to {output_filename}")

if __name__ == "__main__":
    main()
