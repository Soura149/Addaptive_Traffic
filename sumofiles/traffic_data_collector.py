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
# DURATION_XYZ = "10s"
# CARS_ABC = "200total_1000s" 

#2ndddddddddddd
# DURATION_XYZ = "20s"             # The traffic light phase duration you are testing
# CARS_ABC = "200total_1000s"      # Explicitly tracks that it is capped at 200 cars over 1000s

#3rddddddddddd
# DURATION_XYZ = "30s"
# CARS_ABC = "200total_1000s" 

#4thhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "200total_1000s"

#hold ur horsesssssssssssssssss

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
# DURATION_XYZ = "45s"
# CARS_ABC = "800total_1000s_unbalanced" 

#-----------------------------------------------------------
# number of cars changes (number of cars 1200)

#1sttttttttttt
# DURATION_XYZ = "10s"
# CARS_ABC = "1200total_1000s"

#2ndddddddddddd
# DURATION_XYZ = "20s"
# CARS_ABC = "1200total_1000s" 

#3rddddddddddd
# DURATION_XYZ = "30s"
# CARS_ABC = "1200total_1000s" 

#4thhhh
# DURATION_XYZ = "45s"
# CARS_ABC = "1200total_1000s"

#hold ur horsessssssssssssssss
#5thhhhhh
# DURATION_XYZ = "10s"
# CARS_ABC = "1200total_1000s_unbalanced"

#6thhhhh
# DURATION_XYZ = "20s"
# CARS_ABC = "1200total_1000s_unbalanced"

#7thhhhhhhhh
# DURATION_XYZ = "30s"
# CARS_ABC = "1200total_1000s_unbalanced"

#8thhhhhhh
DURATION_XYZ = "45s"
CARS_ABC = "1200total_1000s_unbalanced" 












# Step 5: Define SUMO configuration configuration
# Make the path absolute so the script can be run from outside the sumofiles folder
sumo_cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Traci.sumocfg')

Sumo_config = [
    'sumo-gui',            # Use 'sumo' instead of 'sumo-gui' to run without the UI for faster data collection
    '-c', sumo_cfg_path,   # Path to your SUMO configuration file
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
csv_writer.writerow(['Step', 'Queue_West_East', 'Queue_North_South', 'Queue_SD', 'Arrival_West_East', 'Arrival_North_South', 'Throughput_Step', 'Avg_Waiting_Time_West_East', 'Avg_Waiting_Time_North_South'])

# Step 8: Define Environmental Constants (Updated with discovered lane IDs)
LANE_WEST_EAST = "E0_0"      # Update this if E0_0 is your West-to-East lane
LANE_NORTH_SOUTH = "E1_0"    # Update this if E1_0 is your North-to-South lane

# Step 9: Open connection between SUMO and TraCI
traci.start(Sumo_config)

# Apply dynamic traffic light duration based on DURATION_XYZ
try:
    duration_val = int(DURATION_XYZ.replace("s", ""))
    
    # Get current logic for J2
    logics = traci.trafficlight.getAllProgramLogics("J2")
    logic = logics[0]
    
    # Modify green phase durations (index 0 and 2)
    logic.phases[0].duration = duration_val
    logic.phases[2].duration = duration_val
    
    # Set the updated program back to the traffic light
    traci.trafficlight.setProgramLogic("J2", logic)
    
    print("\n--- VALIDATION: SIGNAL TIMING ---")
    print("Traffic light: J2")
    print(f"WE Green: {duration_val} seconds")
    print(f"WE Yellow: 3 seconds")
    print(f"NS Green: {duration_val} seconds")
    print(f"NS Yellow: 3 seconds")
    print(f"Expected cycle: {duration_val * 2 + 6} seconds")
    print("---------------------------------\n")
except Exception as e:
    print(f"Error applying traffic light duration: {e}")

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
    
    # Extract Directional Arrival Counts
    departed_ids = traci.simulation.getDepartedIDList()
    arrival_we = 0
    arrival_ns = 0
    
    for vid in departed_ids:
        # getRoute returns a tuple of edges this vehicle will traverse
        route = traci.vehicle.getRoute(vid)
        if len(route) > 0:
            start_edge = route[0]
            # E0 is the incoming edge for West-East
            if start_edge == "E0":
                arrival_we += 1
            # E1 is the incoming edge for North-South
            elif start_edge == "E1":
                arrival_ns += 1
                
    # --- 4. Calculate Directional Average Waiting Time ---
    wait_time_we = traci.lane.getWaitingTime(LANE_WEST_EAST)
    wait_time_ns = traci.lane.getWaitingTime(LANE_NORTH_SOUTH)
    
    active_vehicles_we = traci.lane.getLastStepVehicleNumber(LANE_WEST_EAST)
    active_vehicles_ns = traci.lane.getLastStepVehicleNumber(LANE_NORTH_SOUTH)
    
    if active_vehicles_we > 0:
        avg_waiting_time_we = wait_time_we / active_vehicles_we
    else:
        avg_waiting_time_we = 0.0
        
    if active_vehicles_ns > 0:
        avg_waiting_time_ns = wait_time_ns / active_vehicles_ns
    else:
        avg_waiting_time_ns = 0.0

    # --- 5. Save Collected Metrics to CSV Row ---
    csv_writer.writerow([
        step_count, 
        q_we, 
        q_ns, 
        round(q_sd, 4), 
        arrival_we, 
        arrival_ns, 
        arrived_this_step, 
        round(avg_waiting_time_we, 2), 
        round(avg_waiting_time_ns, 2)
    ])

# Step 12: Clean up files and disconnect cleanly
csv_file.close() # Saves and closes the CSV structure safely
traci.close()    # Disconnects TraCI from the SUMO instance cleanly

print(f"Data collection complete! Output saved to: {csv_filename}")