import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import matplotlib.patches as mpatches

def plot_phases(csv_file):
    df = pd.read_csv(csv_file)
    
    phases = []
    current_phase = None
    start_time = None
    duration = 0
    
    for index, row in df.iterrows():
        phase = row['Current_Phase']
        time = row['Sim_Time_s']
        
        if phase != current_phase:
            if current_phase is not None:
                phases.append({'phase': current_phase, 'start': start_time, 'duration': duration})
            current_phase = phase
            start_time = time
            duration = 1
        else:
            duration += 1
    if current_phase is not None:
         phases.append({'phase': current_phase, 'start': start_time, 'duration': duration})

    # Create the figure
    # We make it very wide to accommodate 2000s and 4000s
    fig, ax = plt.subplots(figsize=(20, 4))
    
    we_bars = []
    we_colors = []
    ns_bars = []
    ns_colors = []
    
    # Matching the colors in the user's reference image
    color_map = {
        10: '#4CAF50', # Green
        20: '#3282B8', # Blue
        30: '#FF9800', # Orange
        45: '#D32F2F', # Red
    }
    
    for p in phases:
        c_phase = p['phase']
        dur = p['duration']
        
        # Round the duration to the nearest 10, 20, 30, 45 to handle minor variations
        matched_dur = dur
        if dur <= 12: matched_dur = 10
        elif dur <= 22: matched_dur = 20
        elif dur <= 32: matched_dur = 30
        else: matched_dur = 45
            
        color = color_map.get(matched_dur, '#9E9E9E') # default grey
        
        if c_phase == 'WE_Green':
            we_bars.append((p['start'], dur))
            we_colors.append(color)
        elif c_phase == 'NS_Green':
            ns_bars.append((p['start'], dur))
            ns_colors.append(color)
            
    # Plotting horizontal broken bars
    ax.broken_barh(we_bars, (10, 5), facecolors=we_colors)
    ax.broken_barh(ns_bars, (0, 5), facecolors=ns_colors)
    
    ax.set_ylim(-5, 20)
    ax.set_xlim(0, df['Sim_Time_s'].max())
    ax.set_xlabel('Simulation Time (seconds)', fontsize=12)
    ax.set_yticks([2.5, 12.5])
    ax.set_yticklabels(['North-South Green', 'West-East Green'], fontsize=12, fontweight='bold')
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    
    # Create custom legend
    patches = [mpatches.Patch(color=color_map[k], label=f'{k}s Phase') for k in [10, 20, 30, 45]]
    ax.legend(handles=patches, loc='upper right')
    
    title = os.path.basename(csv_file).replace('.csv', '')
    ax.set_title(f"Signal Phase Execution Window - {title}", fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    out_path = csv_file.replace('.csv', '.png')
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved visualization to {out_path}")

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in {data_dir}")
        return
        
    for f in csv_files:
        plot_phases(f)

if __name__ == '__main__':
    main()
