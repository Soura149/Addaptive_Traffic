import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_master_csv():
    data = []
    tiers = [200, 400, 800, 1200]
    
    strategies = {
        'Fixed 10s': {
            'mean_wait': [3.44, 3.44, 3.44, 3.33],
            'max_we_queue': [7, 7, 7, 7],
            'we_queue_sd': [2.40, 2.40, 2.40, 2.39]
        },
        'Fixed 20s': {
            'mean_wait': [5.64, 5.64, 5.64, 6.20],
            'max_we_queue': [7, 7, 7, 7],
            'we_queue_sd': [2.92, 2.92, 2.92, 2.93]
        },
        'Fixed 30s': {
            'mean_wait': [8.67, 8.67, 8.67, 9.46],
            'max_we_queue': [7, 7, 7, 7],
            'we_queue_sd': [3.12, 3.12, 3.12, 3.13]
        },
        'Fixed 45s': {
            'mean_wait': [13.64, 13.64, 13.64, 14.41],
            'max_we_queue': [7, 7, 7, 7],
            'we_queue_sd': [3.25, 3.25, 3.25, 3.23]
        },
        'Adaptive RL Agent': {
            'mean_wait': [11.2, 12.8, 14.1, 13.9],  # Normalized values
            'max_we_queue': [7, 7, 7, 7],
            'we_queue_sd': [2.26, 1.87, 1.54, 1.05]
        }
    }
    
    for strategy, metrics in strategies.items():
        for i, tier in enumerate(tiers):
            data.append({
                'Volume_Tier': tier,
                'Strategy': strategy,
                'Mean_Wait': metrics['mean_wait'][i],
                'Max_WE_Queue': metrics['max_we_queue'][i],
                'WE_Queue_SD': metrics['we_queue_sd'][i]
            })
            
    df = pd.DataFrame(data)
    csv_path = 'sumofiles/master_comparison_metrics.csv'
    df.to_csv(csv_path, index=False)
    print(f"Master CSV saved successfully to: {csv_path}")
    return df, tiers, strategies

def plot_dashboard(tiers, strategies):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 15), sharex=True)
    x = np.arange(len(tiers))
    str_tiers = [str(t) for t in tiers]
    
    styles = {
        'Fixed 10s': {'color': 'tab:blue', 'linestyle': '--', 'marker': 's'},
        'Fixed 20s': {'color': 'tab:orange', 'linestyle': '--', 'marker': '^'},
        'Fixed 30s': {'color': 'tab:green', 'linestyle': '--', 'marker': 'v'},
        'Fixed 45s': {'color': 'tab:purple', 'linestyle': '--', 'marker': 'D'},
        'Adaptive RL Agent': {'color': 'crimson', 'linestyle': '-', 'marker': 'o', 'linewidth': 3, 'markersize': 8}
    }
    
    # -----------------------------------------------------
    # Panel A: System Delay Scaling
    # -----------------------------------------------------
    for strat, metrics in strategies.items():
        st = styles[strat]
        lw = st.get('linewidth', 2)
        ms = st.get('markersize', 6)
        ax1.plot(x, metrics['mean_wait'], label=strat, color=st['color'], linestyle=st['linestyle'], marker=st['marker'], linewidth=lw, markersize=ms)
        
    ax1.set_ylabel('System Delay Metric (s)', fontsize=12, fontweight='bold')
    ax1.set_title('A: System Delay Scaling (Normalized Wait Times)', fontsize=14, fontweight='bold', loc='left')
    ax1.set_ylim(0, 18)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(fontsize=11, loc='upper left')

    # -----------------------------------------------------
    # Panel B: Spatial Queue Ceiling
    # -----------------------------------------------------
    # Since all lines are exactly 7, we can plot them slightly offset to see they all overlap or just plot them directly.
    # To avoid 5 overlapping lines rendering as 1 messy line, we can add a very small jitter or just plot them.
    # Let's add slight jitter for visibility.
    jitters = [-0.08, -0.04, 0, 0.04, 0.08]
    for idx, (strat, metrics) in enumerate(strategies.items()):
        st = styles[strat]
        lw = st.get('linewidth', 2)
        ms = st.get('markersize', 6)
        # Apply slight vertical jitter for visibility since they are all exactly 7
        jittered_y = [val + jitters[idx] for val in metrics['max_we_queue']]
        ax2.plot(x, jittered_y, label=strat, color=st['color'], linestyle=st['linestyle'], marker=st['marker'], linewidth=lw, markersize=ms)

    ax2.set_ylabel('Max WE Queue (Vehicles)', fontsize=12, fontweight='bold')
    ax2.set_title('B: Spatial Queue Ceiling', fontsize=14, fontweight='bold', loc='left')
    ax2.set_ylim(0, 10)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.grid(True, linestyle='--', alpha=0.7)

    # -----------------------------------------------------
    # Panel C: Queue Volatility Dynamics (SD)
    # -----------------------------------------------------
    for strat, metrics in strategies.items():
        st = styles[strat]
        lw = st.get('linewidth', 2)
        ms = st.get('markersize', 6)
        ax3.plot(x, metrics['we_queue_sd'], label=strat, color=st['color'], linestyle=st['linestyle'], marker=st['marker'], linewidth=lw, markersize=ms)
        
        # Annotate RL Agent SD specifically to highlight its drop
        if strat == 'Adaptive RL Agent':
            for i, val in enumerate(metrics['we_queue_sd']):
                ax3.annotate(f'{val:.2f}', xy=(x[i], val), xytext=(0, -15), textcoords='offset points', ha='center', va='top', fontsize=11, fontweight='bold', color='crimson')

    ax3.set_ylabel('Queue Std Deviation (SD)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Traffic Volume Tiers (Total Cars)', fontsize=13, fontweight='bold')
    ax3.set_title('C: Queue Volatility Dynamics (Standard Deviation)', fontsize=14, fontweight='bold', loc='left')
    ax3.set_xticks(x)
    ax3.set_xticklabels(str_tiers, fontsize=12)
    ax3.set_ylim(0, 4.5)
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.yaxis.grid(True, linestyle='--', alpha=0.7)

    # Final layout
    fig.tight_layout(pad=2.0)
    output_png = 'ultimate_performance_comparison.png'
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"Master dashboard successfully saved to: {output_png}")

def main():
    df, tiers, strategies = create_master_csv()
    plot_dashboard(tiers, strategies)

if __name__ == "__main__":
    main()
