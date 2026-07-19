import os
from pathlib import Path

def get_files_to_delete(workspace_root):
    root = Path(workspace_root)
    
    # Target patterns
    patterns = [
        "**/metrics_dur_*.csv",
        "**/q_table.json",
        "**/decision_log.csv",
        "**/evaluation_log.csv",
        "**/eval_variation_*.csv",
        "**/baseline_*.csv",
        "**/training_episode_summary.csv",
        "**/compiled_agent_metrics.csv",
        "**/master_comparison_metrics.csv",
        "**/evaluation_dump*.csv",
        "**/evaluation_dump*.json"
    ]
    
    # Safe directories that must NOT be touched
    protected_dirs = [
        root / "src",
        # Adding this just in case new_experiment_analytics is moved to root
        root / "new_experiment_analytics" 
    ]
    
    files_to_delete = []
    
    for pattern in patterns:
        for filepath in root.glob(pattern):
            if not filepath.is_file():
                continue
                
            # Check if it's in protected dirs
            is_protected = False
            for p_dir in protected_dirs:
                # If the filepath is a descendant of a protected dir
                if p_dir in filepath.parents:
                    is_protected = True
                    break
            
            if not is_protected:
                files_to_delete.append(filepath)
                
    # Remove duplicates if any patterns overlap
    return list(set(files_to_delete))

def main():
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = get_files_to_delete(workspace_root)
    
    if not files:
        print("No legacy files found to delete outside of safe directories.")
        return
        
    print(f"\nDiscovered {len(files)} legacy files targeted for removal:")
    for f in sorted(files):
        print(f" - {f.relative_to(workspace_root)}")
        
    print("\nProtected Directories (Skipped):")
    print(f" - src\\")
    print(f" - src\\new_experiment_analytics\\")
    
    print("\n---")
    confirmation = input("Do you want to proceed with permanent deletion of the above files? (y/n): ")
    
    if confirmation.lower().strip() == 'y':
        print("\nDeleting legacy files...")
        deleted_count = 0
        for f in sorted(files):
            try:
                f.unlink()
                print(f" [DELETED] {f.relative_to(workspace_root)}")
                deleted_count += 1
            except Exception as e:
                print(f" [FAILED] {f.relative_to(workspace_root)}: {e}")
        
        print(f"\nCleanup complete. Successfully removed {deleted_count}/{len(files)} legacy files.")
        
        # Display streamlined layout
        print("\nStreamlined Repository Directory Layout (High-Level):")
        os.system('tree /A /F "'+ workspace_root +'" | findstr /V /C:"Volume" | findstr /V /C:"Folder PATH"')
    else:
        print("\nDeletion cancelled. No files were modified.")

if __name__ == "__main__":
    main()
