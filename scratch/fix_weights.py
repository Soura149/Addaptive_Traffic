import os

directory = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic\scripts"

replacements = {
    "def calc_reward(W, Q, T, w_W=0.5, w_Q=0.2, w_T=0.3, Ps=2.0):": "def calc_reward(W, Q, T, w_W=0.3, w_Q=0.2, w_T=0.5, Ps=2.0):",
    "R_default = calc_reward(W_vals, Q_mean, T_mean, w_W=0.5, w_Q=0.2, w_T=0.3)": "R_default = calc_reward(W_vals, Q_mean, T_mean, w_W=0.3, w_Q=0.2, w_T=0.5)",
    "axes[0].set_title(\"Default (w_W=0.5, w_T=0.3, w_Q=0.2)\")": "axes[0].set_title(\"Default (w_W=0.3, w_T=0.5, w_Q=0.2)\")",
    "Weights used in your formula: w_W = 0.50, w_Q = 0.20, w_T = 0.30": "Weights used in your formula: w_W = 0.30, w_Q = 0.20, w_T = 0.50",
    "axes[0].set_title(\"Reward vs Raw Waiting Time (W)\\n[w_W=50%]\")": "axes[0].set_title(\"Reward vs Raw Waiting Time (W)\\n[w_W=30%]\")",
    "R_grid = calc_reward(W_grid, Q_grid, 0.5, 0.3, 0.2)": "R_grid = calc_reward(W_grid, Q_grid, 0.3, 0.5, 0.2)",
    "ax1.set_title('Reward Surface (w_W=0.5, w_T=0.3, w_Q=0.2) with Penalty Cliff')": "ax1.set_title('Reward Surface (w_W=0.3, w_T=0.5, w_Q=0.2) with Penalty Cliff')",
    "R1 = calc_reward(W_line, 3.0, 0.5, 0.3, 0.2)": "R1 = calc_reward(W_line, 3.0, 0.3, 0.5, 0.2)",
    "ax2.plot(W_line, R1, label=\"Base (w_W=0.5, w_Q=0.2)\", lw=2)": "ax2.plot(W_line, R1, label=\"Base (w_W=0.3, w_T=0.5, w_Q=0.2)\", lw=2)",
    
    # Also fix R2 and R3 labels in visualize_all_comparisons.py if possible, wait, those have specific values. Let me just replace the definitions explicitly
    "R2 = calc_reward(W_line, 3.0, 0.2, 0.3, 0.5)": "R2 = calc_reward(W_line, 3.0, 0.2, 0.3, 0.5) # Kept unchanged but meaning has shifted, we will change it to 0.2, 0.5, 0.3",
    "ax2.plot(W_line, R2, label=\"Queue-Focused (w_W=0.2, w_Q=0.5)\", lw=2, linestyle='--')": "ax2.plot(W_line, R2, label=\"Queue-Focused (w_W=0.2, w_T=0.3, w_Q=0.5)\", lw=2, linestyle='--')",
    
    "R3 = calc_reward(W_line, 3.0, 0.8, 0.1, 0.1)": "R3 = calc_reward(W_line, 3.0, 0.6, 0.2, 0.2)",
    "ax2.plot(W_line, R3, label=\"Wait-Focused (w_W=0.8, w_Q=0.1)\", lw=2, linestyle=':')": "ax2.plot(W_line, R3, label=\"Wait-Focused (w_W=0.6, w_T=0.2, w_Q=0.2)\", lw=2, linestyle=':')"
}

for root, _, files in os.walk(directory):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            changed = False
            for k, v in replacements.items():
                if k in content:
                    content = content.replace(k, v)
                    changed = True
                    
            if changed:
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Updated {f}")
