import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_volume_reward_comparison():
    # 1. Define traffic volumes to look for
    volumes = [200, 400, 600, 800]
    
    # Dictionaries to store average normalized scores per volume
    queue_scores = []
    throughput_scores = []
    wait_scores = []
    fairness_scores = []
    
    for vol in volumes:
        # Match CSV files corresponding to each volume (e.g., in collected_data/)
        file_pattern = f"collected_data/*{vol}*.csv"
        files = glob.glob(file_pattern)
        
        if not files:
            print(f"[!] Warning: No CSV found for {vol} veh/hr. Filling with dummy zeros.")
            queue_scores.append(0.0)
            throughput_scores.append(0.0)
            wait_scores.append(0.0)
            fairness_scores.append(0.0)
            continue
            
        # Load and aggregate data across matching runs
        df_list = [pd.read_csv(f) for f in files]
        df = pd.concat(df_list, ignore_index=True)
        
        # Extract normalized scores (or calculate them dynamically if raw columns exist)
        # Queue Score: Q_q (1 - Q/Q_max)
        if 'Q_q' in df:
            q_score = df['Q_q'].mean()
        else:
            queue_len = df['Queue_West_East'] + df['Queue_North_South'] if 'Queue_West_East' in df else df.get('queue_length', 0)
            q_score = (1 - queue_len / 9.0).clip(0, 1).mean()
        
        # Throughput Score: T_q (T / T_max)
        if 'T_q' in df:
            t_score = df['T_q'].mean()
        else:
            throughput = df['Throughput_Step'] if 'Throughput_Step' in df else df.get('throughput', 0)
            t_score = (throughput / 1.0).clip(0, 1).mean()
        
        # Wait Score: W_q (1 - W/W_max)
        if 'W_q' in df:
            w_score = df['W_q'].mean()
        else:
            wait_time = df['Avg_Waiting_Time_West_East'] + df['Avg_Waiting_Time_North_South'] if 'Avg_Waiting_Time_West_East' in df else df.get('waiting_time', 0)
            w_score = (1 - wait_time / 327.0).clip(0, 1).mean()
        
        # Fairness Score: Optional 1 - |WE_wait - NS_wait| / total_wait, or fallback calculation
        if 'fairness_score' in df:
            f_score = df['fairness_score'].mean()
        else:
            # Fallback calculation if fairness column isn't present directly
            we_wait = df.get('Avg_Waiting_Time_West_East', df.get('we_max_wait', 0))
            ns_wait = df.get('Avg_Waiting_Time_North_South', df.get('ns_max_wait', 0))
            tot_wait = we_wait + ns_wait + 1e-5
            f_score = (1 - (abs(we_wait - ns_wait) / tot_wait)).clip(0, 1).mean()

        queue_scores.append(np.round(q_score, 2))
        throughput_scores.append(np.round(t_score, 2))
        wait_scores.append(np.round(w_score, 2))
        fairness_scores.append(np.round(f_score, 2))

    # 2. Plotting setup
    x = np.arange(len(volumes))  # Label locations for [200, 400, 600, 800]
    width = 0.18                 # Width of individual bars

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    # Plot grouped bars with matching colors
    rects1 = ax.bar(x - 1.5*width, queue_scores, width, label='Queue Score', color='#FF6347')
    rects2 = ax.bar(x - 0.5*width, throughput_scores, width, label='Throughput Score', color='#2E8B57')
    rects3 = ax.bar(x + 0.5*width, wait_scores, width, label='Wait Score', color='#FFA500')
    rects4 = ax.bar(x + 1.5*width, fairness_scores, width, label='Fairness Score', color='#4682B4')

    # 3. Add numerical value labels on top of every bar
    def add_labels(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 4),  # 4pt vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    add_labels(rects1)
    add_labels(rects2)
    add_labels(rects3)
    add_labels(rects4)

    # 4. Chart formatting
    ax.set_ylabel('Average Score (0 to 1 scale)', fontsize=11)
    ax.set_title('Effect of Traffic Volume on Each Reward Parameter', fontsize=13, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{v} veh/hr' for v in volumes], fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.legend(loc='right', fontsize=10, frameon=True)

    os.makedirs('outputs', exist_ok=True)
    plt.tight_layout()
    output_path = 'outputs/effect_of_traffic_volume_reward_parameters.png'
    plt.savefig(output_path)
    plt.show()
    print(f"✅ Generated grouped bar chart: {output_path}")

if __name__ == '__main__':
    generate_volume_reward_comparison()
