# Step 1: Add modules to provide access to specific libraries, functions, and data handling
import os       # Provides functions to handle file paths, directories, and environment variables
import sys      # Provides access to Python-specific system parameters and functions
import csv      # Used to format, generate, and write data directly into CSV files
import math     # Provides mathematical functions to calculate Standard Deviation

# Step 2: Establish path to SUMO (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Add TraCI module to control the simulation programmatically
import traci














# Step 4: Define Current Configuration Variables (For automatic CSV naming)
# Adjust these values manually for each combo run from your roadmap
# DURATION_XYZ = "20s"       # Traffic light duration for this run (e.g., 10s, 20s, 30s)
# CARS_ABC = "600_balanced"  # Number of cars and flow distribution pattern


# 1sttttttttttttttt
# Step 4: Define Current Configuration Variables (For automatic CSV naming)
# DURATION_XYZ = "20s"             # The traffic light phase duration you are testing
# CARS_ABC = "200total_1000s"      # Explicitly tracks that it is capped at 200 cars over 1000s

#2ndddddddddddd
# DURATION_XYZ = "10s"
# CARS_ABC = "200total_1000s" 

#3rddddddddddd
# DURATION_XYZ = "30s"
# CARS_ABC = "200total_1000s" 

#4thhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "200total_1000s"

#5thhhhhh
# DURATION_XYZ = "10s"
# CARS_ABC = "200total_1000s_unbalanced"

#6thhhhh
# DURATION_XYZ = "20s"
# CARS_ABC = "200total_1000s_unbalanced"

#7thhhhhhhhh
# DURATION_XYZ = "30s"
# CARS_ABC = "200total_1000s_unbalanced"

#8thhhhhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "200total_1000s_unbalanced"

#-----------------------------------------------------------
# number of cars changes (number of cars 600)
#1sttttttttttttttttttttttttttt
# DURATION_XYZ = "10s"
# CARS_ABC = "600total_1000s" 

#2ndddddddddddd
# DURATION_XYZ = "20s"
# CARS_ABC = "600total_1000s" 

#3rddddddddddd
# DURATION_XYZ = "30s"
# CARS_ABC = "600total_1000s" 

#4thhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "600total_1000s"

#hold ur horsessssssssssssssss

#5thhhhhh
# DURATION_XYZ = "10s"
# CARS_ABC = "600total_1000s_unbalanced"

#6thhhhh
# DURATION_XYZ = "20s"
# CARS_ABC = "600total_1000s_unbalanced"

#7thhhhhhhhh
# DURATION_XYZ = "30s"
# CARS_ABC = "600total_1000s_unbalanced"

#8thhhhhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "600total_1000s_unbalanced"  

#-----------------------------------------------------------
# number of cars changes (number of cars 400)
#1sttttttttttttttttttttttttttt
# DURATION_XYZ = "10s"
# CARS_ABC = "400total_1000s" 

#2ndddddddddddd
# DURATION_XYZ = "20s"
# CARS_ABC = "400total_1000s" 

#3rddddddddddd
# DURATION_XYZ = "30s"
# CARS_ABC = "400total_1000s" 

#4thhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "400total_1000s"

#hold ur horsessssssssssssssss
#5thhhhhh
# DURATION_XYZ = "10s"
# CARS_ABC = "400total_1000s_unbalanced"

#6thhhhh
# DURATION_XYZ = "20s"
# CARS_ABC = "400total_1000s_unbalanced"

#7thhhhhhhhh
# DURATION_XYZ = "30s"
# CARS_ABC = "400total_1000s_unbalanced"

#8thhhhhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "400total_1000s_unbalanced" 

#-----------------------------------------------------------
# number of cars changes (number of cars 800)
#1sttttttttttttttttttttttttttt
# DURATION_XYZ = "10s"
# CARS_ABC = "800total_1000s" 

#2ndddddddddddd
# DURATION_XYZ = "20s"
# CARS_ABC = "800total_1000s" 

#3rddddddddddd
# DURATION_XYZ = "30s"
# CARS_ABC = "800total_1000s" 

#4thhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "800total_1000s"

#hold ur horsessssssssssssssss
#5thhhhhh
# DURATION_XYZ = "10s"
# CARS_ABC = "800total_1000s_unbalanced"

#6thhhhh
# DURATION_XYZ = "20s"
# CARS_ABC = "800total_1000s_unbalanced"

#7thhhhhhhhh
# DURATION_XYZ = "30s"
# CARS_ABC = "800total_1000s_unbalanced"

#8thhhhhhh
DURATION_XYZ = "45s"
CARS_ABC = "800total_1000s_unbalanced" 













# Step 5: Define SUMO configuration configuration
Sumo_config = [
    'sumo-gui',            # Use 'sumo' instead of 'sumo-gui' to run without the UI for faster data collection
    '-c', 'Traci.sumocfg', # Path to your SUMO configuration file
    '--step-length', '1.0' # 1-second step size makes calculating time-dependent metrics straightforward
]

# Step 6: Create the Output Directory and Setup CSV Dynamic Naming
output_folder = "collected_data"
if not os.path.exists(output_folder):
    os.makedirs(output_folder) # Creates the folder if it does not exist yet

# Dynamically generate filename using the configuration variables
csv_filename = os.path.join(output_folder, f"metrics_dur_{DURATION_XYZ}_cars_{CARS_ABC}.csv")

# Step 7: Open CSV File and Write the Headers
csv_file = open(csv_filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Step', 'Queue_West_East', 'Queue_North_South', 'Queue_SD', 'Throughput_Step', 'Avg_Waiting_Time'])

# Step 8: Define Environmental Constants (Updated with discovered lane IDs)
LANE_WEST_EAST = "E0_0"      # Update this if E0_0 is your West-to-East lane
LANE_NORTH_SOUTH = "E1_0"    # Update this if E1_0 is your North-to-South lane

# Step 9: Open connection between SUMO and TraCI
traci.start(Sumo_config)

# --- ADD THESE THREE LINES TEMPORARILY TO FIND YOUR IDS ---
# print("\n--- DETECTED LANES IN YOUR NETWORK ---")
# print(traci.lane.getIDList())
# print("--------------------------------------\n")

# Step 10: Initialize Tracking Variables
step_count = 0
total_departed_vehicles = set() # Keeps track of unique vehicle IDs that entered the map
total_arrived_vehicles = 0      # Counts how many vehicles left the network completely

# Step 11: Execute Simulation Loop step-by-step
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep() 
    step_count += 1
    
    # --- 1. Extract Queue Lengths ---
    # getHaltingNumber returns the count of vehicles moving slower than 0.1 m/s on that lane
    q_we = traci.lane.getLastStepHaltingNumber(LANE_WEST_EAST)
    q_ns = traci.lane.getLastStepHaltingNumber(LANE_NORTH_SOUTH)
    
    # --- 2. Calculate Standard Deviation (SD) of Queues Manually ---
    mean_q = (q_we + q_ns) / 2
    variance = ((q_we - mean_q) ** 2 + (q_ns - mean_q) ** 2) / 2
    q_sd = math.sqrt(variance)
    
    # --- 3. Extract Throughput ---
    # Arrived vehicle IDs are collected from the simulation layer at the exact frame they exit
    arrived_this_step = traci.simulation.getArrivedNumber()
    
    # --- 4. Calculate Average Waiting Time ---
    # getWaitingTime returns the total accumulated time spent halting for all vehicles on a lane
    wait_time_we = traci.lane.getWaitingTime(LANE_WEST_EAST)
    wait_time_ns = traci.lane.getWaitingTime(LANE_NORTH_SOUTH)
    
    # Count total active vehicles currently on both lanes to find an accurate average
    active_vehicles = traci.lane.getLastStepVehicleNumber(LANE_WEST_EAST) + traci.lane.getLastStepVehicleNumber(LANE_NORTH_SOUTH)
    
    if active_vehicles > 0:
        avg_waiting_time = (wait_time_we + wait_time_ns) / active_vehicles
    else:
        avg_waiting_time = 0.0 # Avoid division by zero when the intersection is clear

    # --- 5. Save Collected Metrics to CSV Row ---
    csv_writer.writerow([step_count, q_we, q_ns, round(q_sd, 4), arrived_this_step, round(avg_waiting_time, 2)])

# Step 12: Clean up files and disconnect cleanly
csv_file.close() # Saves and closes the CSV structure safely
traci.close()    # Disconnects TraCI from the SUMO instance cleanly

print(f"Data collection complete! Output saved to: {csv_filename}")