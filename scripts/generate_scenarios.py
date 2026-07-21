import os
import random
from pathlib import Path

def generate_route_file(filepath, num_we, num_ns, duration=1000.0):
    we_times = sorted([round(random.uniform(0, duration), 2) for _ in range(num_we)])
    ns_times = sorted([round(random.uniform(0, duration), 2) for _ in range(num_ns)])
    
    # Merge and sort vehicles
    vehicles = []
    for i, t in enumerate(we_times):
        vehicles.append({'id': f'we_{i}', 'type': 'car', 'route': 'route_we', 'depart': t, 'departLane': '0'})
    for i, t in enumerate(ns_times):
        vehicles.append({'id': f'ns_{i}', 'type': 'car', 'route': 'route_ns', 'depart': t, 'departLane': '0'})
        
    vehicles.sort(key=lambda x: x['depart'])
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        f.write('    <vType id="car" maxSpeed="13.89" length="4.7"/>\n')
        f.write('    <route id="route_we" edges="E0 E0.58"/>\n')
        f.write('    <route id="route_ns" edges="E1 E2"/>\n')
        for v in vehicles:
            f.write(f'    <vehicle id="{v["id"]}" type="{v["type"]}" route="{v["route"]}" depart="{v["depart"]}" departLane="{v["departLane"]}"/>\n')
        f.write('</routes>\n')

def main():
    base_dir = Path(r"C:\VSCODE\CISInternship_Implement")
    routes_dir = base_dir / "sumofiles" / "routes"
    
    scenarios = [
        ("s1_low_200.rou.xml", 150, 50),
        ("s2_medium_600.rou.xml", 450, 150),
        ("s3_heavy_asym_1200.rou.xml", 900, 300),
        ("s4_heavy_sym_1200.rou.xml", 600, 600),
        ("s5_peak_1800.rou.xml", 1200, 600)
    ]
    
    for filename, we, ns in scenarios:
        filepath = routes_dir / filename
        generate_route_file(filepath, we, ns)
        print(f"Generated {filename}: {we} WE, {ns} NS")

if __name__ == '__main__':
    main()
