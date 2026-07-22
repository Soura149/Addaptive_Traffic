import os
import random

SCENARIOS = {
    "s1_low_200": {"we": 150, "ns": 50},
    "s2_medium_600": {"we": 450, "ns": 150},
    "s3_heavy_asym_1200": {"we": 900, "ns": 300},
    "s4_heavy_sym_1200": {"we": 600, "ns": 600},
    "s5_peak_1800": {"we": 1200, "ns": 600},
}

ROUTES_DIR = os.path.join(os.path.dirname(__file__), "..", "sumofiles", "routes")
TIME_WINDOW = 1000.0

def generate_route_file(scenario_name, counts):
    filename = f"{scenario_name}.rou.xml"
    filepath = os.path.join(ROUTES_DIR, filename)
    
    vehicles = []
    
    # Generate WE vehicles
    for i in range(counts["we"]):
        depart_time = round(random.uniform(0, TIME_WINDOW), 2)
        vehicles.append((depart_time, "we", i))
        
    # Generate NS vehicles
    for i in range(counts["ns"]):
        depart_time = round(random.uniform(0, TIME_WINDOW), 2)
        vehicles.append((depart_time, "ns", i))
        
    # Sort vehicles by depart time
    vehicles.sort(key=lambda x: x[0])
    
    # Write to file
    with open(filepath, "w") as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        f.write('    <vType id="car" maxSpeed="13.89" length="4.7"/>\n')
        f.write('    <route id="route_we" edges="E0 E0.58"/>\n')
        f.write('    <route id="route_ns" edges="E1 E2"/>\n')
        
        for depart_time, direction, idx in vehicles:
            f.write(f'    <vehicle id="{direction}_{idx}" type="car" route="route_{direction}" depart="{depart_time}" departLane="0"/>\n')
            
        f.write('</routes>\n')

    print(f"Generated {filename}: {counts['we']} WE, {counts['ns']} NS.")

def main():
    os.makedirs(ROUTES_DIR, exist_ok=True)
    print("Generating scenarios...")
    for name, counts in SCENARIOS.items():
        generate_route_file(name, counts)
    print("All scenarios generated successfully.")

if __name__ == "__main__":
    main()
