import os
import glob
import csv
from pathlib import Path

def main():
    base_dir = Path(r"C:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic")
    data_dir = base_dir / "collected_data"
    
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    print("="*60)
    print("INVENTORY SCAN: HISTORICAL DATASETS")
    print("="*60)
    
    unique_scenarios = set()
    durations = set()
    
    headers = None
    
    for filepath in csv_files:
        filename = os.path.basename(filepath)
        
        # Example: metrics_dur_10s_cars_200total_1000s.csv
        # or metrics_dur_10s_cars_200total_1000s_unbalanced.csv
        
        parts = filename.replace('.csv', '').split('_')
        
        # Extract duration
        duration = None
        for p in parts:
            if p.endswith('s') and p[:-1].isdigit() and not p.endswith('1000s'):
                duration = p
                durations.add(duration)
                
        # Extract cars
        cars = None
        for p in parts:
            if p.endswith('total'):
                cars = int(p.replace('total', ''))
                
        # Extract balance
        balance = "unbalanced" if "unbalanced" in parts else "balanced"
        
        if cars is not None:
            unique_scenarios.add((cars, balance))
            
        # Get headers from first file
        if headers is None:
            with open(filepath, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
    print(f"Found {len(csv_files)} baseline CSV files.")
    print(f"Unique fixed signal durations: {sorted(list(durations))}")
    print("\nUnique Traffic Scenarios (Cars, Balance):")
    for cars, balance in sorted(list(unique_scenarios)):
        print(f" - {cars} vehicles, {balance} traffic")
        
    print(f"\nExtracted Baseline Column Headers ({len(headers)} columns):")
    for i, h in enumerate(headers):
        print(f" {i+1}. {h}")
        
if __name__ == '__main__':
    main()
