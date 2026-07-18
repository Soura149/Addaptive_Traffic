import pandas as pd
import matplotlib.pyplot as plt

def main():
    # 1. Read the compiled data
    df = pd.read_csv('sumofiles/compiled_agent_metrics.csv')
    
    # Extract data for plotting
    tiers = df['Car Tier'].astype(str).tolist()
    mean_wait = df['Mean Waiting Time'].tolist()

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(9, 6))

    # 2. Plot line chart with requested style
    ax.plot(tiers, mean_wait, color='crimson', marker='o', markersize=8, linewidth=2, label='Avg Waiting Time')

    # Add labels and title
    ax.set_xlabel('Traffic Volume Tiers (Total Cars)', fontsize=12)
    ax.set_ylabel('Average Waiting Time (Seconds)', fontsize=12)
    ax.set_title('Agent Scaling Delay: Average Waiting Time Across Traffic Volumes', fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(tiers)))
    ax.set_xticklabels(tiers, fontsize=11)
    
    # 4. Style matching previous chart (light gray dashed horizontal grids)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    
    # Set y-axis slightly larger for text placement
    ax.set_ylim(0, max(mean_wait) * 1.15)

    # 3. Attach a text label above each marker with exact scaling delay numbers
    for i, wait_time in enumerate(mean_wait):
        ax.annotate(f'{wait_time:.2f}',
                    xy=(i, wait_time),
                    xytext=(0, 10),  # 10 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=12, fontweight='bold', color='black')

    fig.tight_layout()

    # 5. Output file
    output_filename = 'agent_evaluation_waiting_time.png'
    plt.savefig(output_filename, dpi=300)
    print(f"Success: Graph saved cleanly to {output_filename}")

if __name__ == "__main__":
    main()
