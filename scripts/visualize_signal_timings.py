import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap

def main():
    # Load the data
    file_path = "outputs/decision_log.csv"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    df_all = pd.read_csv(file_path)
    last_ep = df_all['episode'].max()
    df = df_all[df_all['episode'] == last_ep].copy()
    df.reset_index(drop=True, inplace=True)
    
    os.makedirs("outputs/visualizations", exist_ok=True)
    
    # Pre-process time spans for Gantt Chart
    # Each row gives the sim_time at the END of the cycle.
    prev_time = 0
    
    we_spans = []
    ns_spans = []
    
    # We will also track for the second plot
    we_durations = []
    ns_durations = []
    we_queues = []
    ns_queues = []
    decision_steps = []
    
    for i, row in df.iterrows():
        # alternating phases
        action_dur = row['action']
        
        we_q = row['we_queue']
        ns_q = row['ns_queue']
        
        if i % 2 == 0:
            # WE Green
            we_green = action_dur
            ns_green = 0
            
            we_start = prev_time
            we_end = we_start + we_green
            we_spans.append((we_start, we_green))
            prev_time = we_end + 3 # yellow time
        else:
            # NS Green
            we_green = 0
            ns_green = action_dur
            
            ns_start = prev_time
            ns_end = ns_start + ns_green
            ns_spans.append((ns_start, ns_green))
            prev_time = ns_end + 3
        
        decision_steps.append(i + 1)
        we_durations.append(we_green)
        ns_durations.append(ns_green)
        we_queues.append(we_q)
        ns_queues.append(ns_q)
        
    # -------------------------------------------------------------
    # Plot 1: Clean Zoomed-In High-Resolution Gantt Chart (0-400s)
    # -------------------------------------------------------------
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(12, 3), dpi=300)
    
    colors = {10: '#2ca02c', 20: '#1f77b4', 30: '#ff7f0e', 45: '#d62728'}
    
    for (start, duration) in we_spans:
        if start > 400: continue
        c = colors.get(duration, '#7f7f7f')
        ax.barh(1, duration, left=start, height=0.5, color=c, edgecolor='none', alpha=0.85)
        
    for (start, duration) in ns_spans:
        if start > 400: continue
        c = colors.get(duration, '#7f7f7f')
        ax.barh(0, duration, left=start, height=0.5, color=c, edgecolor='none', alpha=0.85)
        
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['North-South Green', 'West-East Green'], fontsize=11, fontweight='bold')
    ax.set_xlabel('Simulation Time (seconds)', fontsize=11)
    ax.set_title('Signal Phase Execution Window (t = 0s to 400s)', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 400)
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    
    # Custom Legend
    patches_legend = [mpatches.Patch(color=col, label=f'{dur}s Phase') for dur, col in colors.items()]
    ax.legend(handles=patches_legend, loc='upper right', frameon=True)
    
    plt.tight_layout()
    plt.savefig('outputs/visualizations/clean_signal_timeline.png')
    plt.close()
    
    # -------------------------------------------------------------
    # Plot 2: Dynamic Duration Allocation Over Time
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Top subplot: WE Green Duration and Queue
    ax1.plot(decision_steps, we_durations, 'bo-', label='WE Green Duration (s)', linewidth=2, markersize=6)
    ax1.set_ylabel('Green Duration (s)', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.set_yticks([10, 20, 30, 45])
    
    ax1_twin = ax1.twinx()
    ax1_twin.fill_between(decision_steps, we_queues, color='red', alpha=0.3, label='WE Queue Length')
    ax1_twin.plot(decision_steps, we_queues, 'r--', alpha=0.7)
    ax1_twin.set_ylabel('Queue Length (Vehicles)', color='r')
    ax1_twin.tick_params(axis='y', labelcolor='r')
    
    ax1.set_title('West-East: Dynamic Duration Allocation vs Queue Length')
    
    # Ask matplotlib to put both legends together
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    # Bottom subplot: NS Green Duration and Queue
    ax2.plot(decision_steps, ns_durations, 'go-', label='NS Green Duration (s)', linewidth=2, markersize=6)
    ax2.set_ylabel('Green Duration (s)', color='g')
    ax2.tick_params(axis='y', labelcolor='g')
    ax2.set_yticks([10, 20, 30, 45])
    
    ax2_twin = ax2.twinx()
    ax2_twin.fill_between(decision_steps, ns_queues, color='orange', alpha=0.4, label='NS Queue Length')
    ax2_twin.plot(decision_steps, ns_queues, 'o--', color='orange', alpha=0.7)
    ax2_twin.set_ylabel('Queue Length (Vehicles)', color='orange')
    ax2_twin.tick_params(axis='y', labelcolor='orange')
    
    ax2.set_title('North-South: Dynamic Duration Allocation vs Queue Length')
    ax2.set_xlabel('Decision Step')
    
    lines3, labels3 = ax2.get_legend_handles_labels()
    lines4, labels4 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines3 + lines4, labels3 + labels4, loc='upper left')

    plt.tight_layout()
    plt.savefig('outputs/visualizations/phase_durations_over_time.png', dpi=300)
    plt.close()
    
    print("Verification Summary:")
    print(f"- Parsed CSV: {file_path}")
    print(f"- Total Decision Steps: {len(decision_steps)}")
    print(f"- Max Sim Time: {prev_time} seconds")
    print(f"- Generated: outputs/visualizations/clean_signal_timeline.png")
    print(f"- Generated: outputs/visualizations/phase_durations_over_time.png")
    
if __name__ == '__main__':
    main()
