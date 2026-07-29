import os
import xml.etree.ElementTree as ET

def verify_environment():
    base_dir = r"c:\VSCODE\cis_internshipmodel2.0\Addaptive_Traffic"
    routes_dir = os.path.join(base_dir, "sumofiles", "routes")
    net_file = os.path.join(base_dir, "sumofiles", "Traci.net.xml")
    sumocfg_file = os.path.join(base_dir, "src", "Traci.sumocfg")
    
    vols = [100, 300, 600, 900, 1200]
    matrix = {}
    
    # Check 1: 25 Generated Scenario Route Files
    print("--- Route Files Verification ---")
    all_correct = True
    for we_vol in vols:
        matrix[we_vol] = {}
        for ns_vol in vols:
            filename = f"route_we_{we_vol}_ns_{ns_vol}.rou.xml"
            filepath = os.path.join(routes_dir, filename)
            
            if not os.path.exists(filepath):
                matrix[we_vol][ns_vol] = "MISSING"
                all_correct = False
                continue
                
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            we_count = sum(1 for v in root.findall('vehicle') if v.get('route') == 'route_we')
            ns_count = sum(1 for v in root.findall('vehicle') if v.get('route') == 'route_ns')
            
            if we_count == we_vol and ns_count == ns_vol:
                matrix[we_vol][ns_vol] = "OK"
            else:
                matrix[we_vol][ns_vol] = f"FAIL (WE:{we_count}, NS:{ns_count})"
                all_correct = False
                
    if all_correct:
        print("All 25 scenario files verified successfully.")
    
    # Check 2: Traffic light phases
    print("\n--- Traffic Light Phases Verification ---")
    tree = ET.parse(net_file)
    root = tree.getroot()
    tl = root.find(".//tlLogic[@id='J2']")
    if tl is not None:
        phases = tl.findall('phase')
        if len(phases) == 4:
            print(f"Phase 0: {phases[0].get('state')} (Duration: {phases[0].get('duration')}) - WE Green")
            print(f"Phase 1: {phases[1].get('state')} (Duration: {phases[1].get('duration')}) - WE Yellow 3s")
            print(f"Phase 2: {phases[2].get('state')} (Duration: {phases[2].get('duration')}) - NS Green")
            print(f"Phase 3: {phases[3].get('state')} (Duration: {phases[3].get('duration')}) - NS Yellow 3s")
            
            # Check phases explicitly
            checks = [
                phases[0].get('state') == 'GGrr',
                phases[1].get('state') == 'yyrr' and phases[1].get('duration') == '3',
                phases[2].get('state') == 'rrGG',
                phases[3].get('state') == 'rryy' and phases[3].get('duration') == '3'
            ]
            if all(checks):
                print("Traffic light phases verified correctly.")
            else:
                print("Traffic light phases DO NOT MATCH expected configuration.")
        else:
            print("Incorrect number of phases.")
    else:
        print("tlLogic J2 not found.")
        
    # Check 3: Relative config paths
    print("\n--- Configuration Path Verification ---")
    tree = ET.parse(sumocfg_file)
    root = tree.getroot()
    cfg_dir = os.path.dirname(sumocfg_file)
    
    input_node = root.find('input')
    net_val = input_node.find('net-file').get('value')
    route_val = input_node.find('route-files').get('value')
    
    net_path = os.path.abspath(os.path.join(cfg_dir, net_val))
    route_path = os.path.abspath(os.path.join(cfg_dir, route_val))
    
    print(f"Configured net-file: {net_val}")
    print(f"Resolved net-file path: {net_path} (Exists: {os.path.exists(net_path)})")
    
    print(f"Configured route-files: {route_val}")
    print(f"Resolved route-files path: {route_path} (Exists: {os.path.exists(route_path)})")
    
    if os.path.exists(net_path) and os.path.exists(route_path):
        print("Path resolution verified correctly.")
        
    print("\n--- 5x5 Verification Matrix Table ---")
    header = "WE/NS" + "".join([f"| {v:<4}" for v in vols])
    print(header)
    print("-" * len(header))
    for we_vol in vols:
        row = f"{we_vol:<5}"
        for ns_vol in vols:
            status = matrix[we_vol][ns_vol]
            row += f"| {status:<4}"
        print(row)

if __name__ == "__main__":
    verify_environment()
