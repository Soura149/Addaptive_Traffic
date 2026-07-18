import os
import shutil

def move_files(src_dir, files, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for f in files:
        src_path = os.path.join(src_dir, f)
        dest_path = os.path.join(dest_dir, f)
        if os.path.exists(src_path):
            shutil.move(src_path, dest_path)
            print(f"Moved {f} to {dest_dir}/")
        else:
            print(f"Warning: File not found: {src_path}")

def main():
    # 1. Move to src/
    src_from_sumo = [
        "q_learning_agent.py", "test_variations.py", "run_experiments.py", 
        "route_generator.py", "traffic_data_collector.py",
        "Traci.net.xml", "Traci.netecfg", "Traci.rou.xml", "Traci.sumocfg", "test.rou.xml"
    ]
    move_files("sumofiles", src_from_sumo, "src")

    # 2. Move to scripts/
    scripts_from_root = [
        "calculate_eval_statistics.py", "compile_evaluation_data.py", 
        "extract_all_baseline_stats.py", "extract_baselines.py",
        "filecount.py", "print_tree.py",
        "scratch_check.py", "scratch_check_1200.py", 
        "scratch_littles_law.py", "scratch_mean_wait.py"
    ]
    move_files(".", scripts_from_root, "scripts")

    # 3. Move to analysis/
    analysis_from_root = [
        "plot_evaluation_queues.py", "plot_evaluation_waiting_time.py", 
        "plot_final_comparison.py", "plot_master_evaluation.py", 
        "plot_master_evaluation_metrics.py", "plot_ultimate_comparison_dashboard.py", 
        "visualize_results.py"
    ]
    move_files(".", analysis_from_root, "analysis")

    # 4. Move to outputs/
    outputs_from_root = [
        "agent_comprehensive_evaluation.png", "agent_evaluation_queues.png", 
        "agent_evaluation_waiting_time.png", "agent_master_evaluation.png", 
        "performance_comparison_matrix.png", "ultimate_performance_comparison.png", 
        "chart1_comprehensive_performance.png", "chart2_asymmetric_stability.png", 
        "chart3_reward_convergence.png", "chart4_reward_parameter_sensitivity.png"
    ]
    move_files(".", outputs_from_root, "outputs")

    outputs_from_sumo = [
        "compiled_agent_metrics.csv", "master_comparison_metrics.csv"
    ]
    move_files("sumofiles", outputs_from_sumo, "outputs")

    print("\nRefactoring complete.")

if __name__ == "__main__":
    main()
