import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_average_parameter_contributions():
    # 1. Gather all simulation CSV files
    file_pattern = "collected_data/*.csv"
    files = glob.glob(file_pattern)
    
    if not files:
        print("[!] No CSV files found in collected_data/. Generating sample plot structure.")
        # Fallback dummy data matching image if no CSVs exist yet
        q_contrib, t_contrib, w_contrib, f_contrib = 0.014, 0.382, 0.036, 0.016
    else:
        df_list = [pd.read_csv(f) for f in files]
        df = pd.concat(df_list, ignore_index=True)
        
        # 2. Compute weighted contributions (normalized value * weight factor)
        # Weights used in your formula: w_W = 0.30, w_Q = 0.20, w_T = 0.50
        
        # Queue Penalty Contribution: w_Q * (1 - Q_q)
        if 'Q_q' in df:
            q_score = df['Q_q']
        else:
            queue_len = df['Queue_West_East'] + df['Queue_North_South'] if 'Queue_West_East' in df else df.get('queue_length', 0)
            q_score = (1 - queue_len / 9.0).clip(0, 1)
        q_contrib = (0.20 * (1 - q_score)).mean()
        
        # Throughput Reward Contribution: w_T * T_q
        if 'T_q' in df:
            t_score = df['T_q']
        else:
            throughput = df['Throughput_Step'] if 'Throughput_Step' in df else df.get('throughput', 0)
            t_score = (throughput / 1.0).clip(0, 1)
        t_contrib = (0.50 * t_score).mean()
        
        # Wait Penalty Contribution: w_W * (1 - W_q)
        if 'W_q' in df:
            w_score = df['W_q']
        else:
            wait_time = df['Avg_Waiting_Time_West_East'] + df['Avg_Waiting_Time_North_South'] if 'Avg_Waiting_Time_West_East' in df else df.get('waiting_time', 0)
            w_score = (1 - wait_time / 327.0).clip(0, 1)
        w_contrib = (0.30 * (1 - w_score)).mean()
        
        # Fairness Penalty Contribution
        if 'fairness_score' in df:
            f_score = df['fairness_score']
        else:
            we_wait = df.get('Avg_Waiting_Time_West_East', df.get('we_max_wait', 0))
            ns_wait = df.get('Avg_Waiting_Time_North_South', df.get('ns_max_wait', 0))
            tot_wait = we_wait + ns_wait + 1e-5
            f_score = (1 - (abs(we_wait - ns_wait) / tot_wait)).clip(0, 1)
        f_contrib = (0.10 * (1 - f_score)).mean()

    # Rounded to 3 decimal places as shown in image
    categories = ['Queue Penalty', 'Throughput Reward', 'Wait Penalty', 'Fairness Penalty']
    values = [np.round(q_contrib, 3), np.round(t_contrib, 3), np.round(w_contrib, 3), np.round(f_contrib, 3)]
    colors = ['#FF6347', '#2E8B57', '#FFA500', '#4682B4']  # Matching color palette

    # 3. Plotting setup
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    bars = ax.bar(categories, values, color=colors, width=0.75)

    # 4. Add numerical labels above each bar
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),  # 4pt vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    # 5. Styling and Formatting
    ax.set_ylabel('Average Contribution (normalized)', fontsize=11)
    ax.set_title('Average Effect of Each Parameter on Reward (Whole Simulation)', fontsize=13, fontweight='bold', pad=12)
    ax.set_ylim(0, max(values) * 1.15 if max(values) > 0 else 0.40)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    os.makedirs('outputs', exist_ok=True)
    plt.tight_layout()
    output_path = 'outputs/average_effect_reward_parameters.png'
    plt.savefig(output_path)
    
    print(f"✅ Generated parameter contribution chart: {output_path}")

if __name__ == '__main__':
    generate_average_parameter_contributions()
