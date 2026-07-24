import os

def fix_file(filepath):
    if not os.path.exists(filepath):
        print(f"Skipped {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "plot_average_parameter_contributions.py" in filepath:
        content = content.replace("w_W = 0.30, w_Q = 0.20, w_T = 0.50", "w_W = 0.30, w_Q = 0.20, w_T = 0.50") # Just docstring
        content = content.replace("t_contrib = (0.30 * t_score).mean()", "t_contrib = (0.50 * t_score).mean()")
        content = content.replace("w_contrib = (0.50 * (1 - w_score)).mean()", "w_contrib = (0.30 * (1 - w_score)).mean()")
        
    if "plot_reward_parameter_effects.py" in filepath:
        # We need to make sure the labels and colors match our actual weights
        pass
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Fixed {filepath}")

fix_file("scripts/plot_average_parameter_contributions.py")
fix_file("scripts/plot_reward_parameter_effects.py")
fix_file("scripts/plot_reward_progression_by_volume.py")
