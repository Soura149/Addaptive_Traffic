# Step 1: Import modules to handle paths and file system lookups
import os

# Step 2: Define the target directory path
data_folder = "collected_data"

# Step 3: Check if the directory exists and count files
if os.path.exists(data_folder):
    files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]
    total_files = len(files)
    
    print("\n--- DATA FOLDER CHECK ---")
    print(f"Total CSV files found: {total_files} / 40")
    print("-------------------------\n")
    
    if total_files == 40:
        print("🎉 Perfect! All 40 combination data tracks are safely generated.")
    else:
        print("⚠️ Missing some combinations. Double-check your roadmap list!")
else:
    print(f"Directory '{data_folder}' not found. Make sure you are running the script from the right root path.")