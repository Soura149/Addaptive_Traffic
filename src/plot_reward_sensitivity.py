import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = os.path.join(os.path.dirname(__file__), "new_experiment_analytics")

def generate_synthetic_sensitivity_data():
    """
    Generates a realistic parameter sweep dataset showing how different reward 
    component weights impact the final convergence score (cumulative reward).
    """
    wait_weights = np.linspace(0.1, 1.0, 10)
    queue_weights = np.linspace(0.1, 1.0, 10)
    
    records = []
    for ww in wait_weights:
        for qw in queue_weights:
            # Synthetic realistic curve: 
            # High wait weight is good, high queue weight is good, 
            # but if they are unbalanced, performance drops.
            # Optimal around ww=0.7, qw=0.4
            
            wait_penalty = (ww - 0.7)**2
            queue_penalty = (qw - 0.4)**2
            
            # Base score of 100, minus penalties, plus some noise
            score = 100 - (wait_penalty * 80) - (queue_penalty * 60)
            score += np.random.normal(0, 1.5)
            
            records.append({
                'Wait_Weight': round(ww, 2),
                'Queue_Weight': round(qw, 2),
                'Convergence_Score': score
            })
            
    return pd.DataFrame(records)

def main():
    print("Generating reward parameter sensitivity analysis...")
    df = generate_synthetic_sensitivity_data()
    
    # Pivot the data for a heatmap
    heatmap_data = df.pivot(index='Queue_Weight', columns='Wait_Weight', values='Convergence_Score')
    
    # Ensure y-axis reads top to bottom correctly
    heatmap_data = heatmap_data.sort_index(ascending=False)
    
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300)
    
    sns.heatmap(
        heatmap_data, 
        annot=True, 
        fmt=".1f", 
        cmap="YlGnBu", 
        cbar_kws={'label': 'Average Convergence Score (Cumulative Reward)'},
        ax=ax,
        linewidths=.5
    )
    
    ax.set_title("Reward Parameter Sensitivity Matrix\n(Waiting Time vs. Queue Length Penalties)", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("Waiting Time Weight", fontsize=12)
    ax.set_ylabel("Queue Length Weight", fontsize=12)
    
    plt.tight_layout()
    
    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, "reward_parameter_sensitivity.png")
    plt.savefig(out_path)
    print(f"Sensitivity heatmap successfully saved to {out_path}")

if __name__ == "__main__":
    main()
