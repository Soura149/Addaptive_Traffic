import os
import random

def generate_scenarios():
    vols = [100, 300, 600, 900, 1200]
    # Use absolute path based on workspace
    base_dir = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"
    out_dir = os.path.join(base_dir, "sumofiles", "routes")

    os.makedirs(out_dir, exist_ok=True)

    for we_vol in vols:
        for ns_vol in vols:
            filename = f"route_we_{we_vol}_ns_{ns_vol}.rou.xml"
            filepath = os.path.join(out_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write('<routes>\n')
                f.write('    <vType id="car" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" guiShape="passenger"/>\n')
                f.write('    <route id="route_we" edges="E0 E0.58"/>\n')
                f.write('    <route id="route_ns" edges="E1 E2"/>\n')
                
                # Generate sorted random departure times
                we_departs = sorted([round(random.uniform(0, 1000), 2) for _ in range(we_vol)])
                ns_departs = sorted([round(random.uniform(0, 1000), 2) for _ in range(ns_vol)])
                
                for i, depart in enumerate(we_departs):
                    f.write(f'    <vehicle id="we_{i}" type="car" route="route_we" depart="{depart}"/>\n')
                
                for i, depart in enumerate(ns_departs):
                    f.write(f'    <vehicle id="ns_{i}" type="car" route="route_ns" depart="{depart}"/>\n')
                    
                f.write('</routes>\n')

    print("Generated 25 route files.")

if __name__ == "__main__":
    generate_scenarios()
