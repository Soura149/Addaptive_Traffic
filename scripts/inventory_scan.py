import os
from pathlib import Path

def main():
    workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = Path(workspace_root)
    
    # Categories
    active_code = []
    legacy_scripts = []
    redundant_routes = []
    live_config = []
    
    # 1. Active Code (src/*.py)
    src_dir = root / "src"
    if src_dir.exists():
        for py_file in src_dir.glob("*.py"):
            active_code.append(py_file.relative_to(root))
            
    # 2. Legacy Scripts (analysis/, scripts/, scratch_*.py)
    analysis_dir = root / "analysis"
    if analysis_dir.exists():
        for py_file in analysis_dir.glob("*.py"):
            legacy_scripts.append(py_file.relative_to(root))
            
    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.glob("*.py"):
            legacy_scripts.append(py_file.relative_to(root))
            
    # 3. Routes
    # Redundant
    root_route = root / "Traci.rou.xml"
    if root_route.exists():
        redundant_routes.append(root_route.relative_to(root))
        
    test_route = root / "src" / "test.rou.xml"
    if test_route.exists():
        redundant_routes.append(test_route.relative_to(root))
        
    # Live
    live_route = root / "src" / "Traci.rou.xml"
    if live_route.exists():
        live_config.append(live_route.relative_to(root))
        
    print("\n========================================================")
    print(" DRY-RUN INVENTORY: NON-DESTRUCTIVE SAFETY SCAN ")
    print("========================================================\n")
    
    print("[SAFE] ACTIVE PRODUCTION CODE (Must NEVER be altered/moved):")
    for f in sorted(active_code):
        print(f"  + {f}")
        
    print("\n[SAFE] LIVE CONFIGURATION (Preserve):")
    for f in sorted(live_config):
        print(f"  + {f}")
        
    print("\n[FLAGGED] LEGACY SCRIPTS & SCRATCHPADS (analysis/ and scripts/):")
    for f in sorted(legacy_scripts):
        if "inventory_scan.py" in str(f) or "purge_old_experiments.py" in str(f):
            print(f"  ~ {f} (Utility script)")
        elif "scratch" in str(f):
            print(f"  - {f} (Experimental Scratchpad)")
        else:
            print(f"  - {f} (Historical/Duplicate Script)")
            
    print("\n[FLAGGED] REDUNDANT ROUTE FILES (Targeted for removal):")
    for f in sorted(redundant_routes):
        print(f"  - {f}")
        
    print("\n========================================================")
    print(" SCAN COMPLETE - ZERO FILES MODIFIED OR MOVED.")
    print("========================================================")

if __name__ == "__main__":
    main()
