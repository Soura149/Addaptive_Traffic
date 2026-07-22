import os
import xml.etree.ElementTree as ET

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "..")

SCENARIOS = {
    "s1_low_200": {"we": 150, "ns": 50},
    "s2_medium_600": {"we": 450, "ns": 150},
    "s3_heavy_asym_1200": {"we": 900, "ns": 300},
    "s4_heavy_sym_1200": {"we": 600, "ns": 600},
    "s5_peak_1800": {"we": 1200, "ns": 600},
}

def verify_scenarios():
    print("--- Scenario Route Verification ---")
    all_passed = True
    routes_dir = os.path.join(WORKSPACE_DIR, "sumofiles", "routes")
    
    print(f"{'Scenario':<20} | {'Expected WE':<12} | {'Actual WE':<10} | {'Expected NS':<12} | {'Actual NS':<10} | {'Status'}")
    print("-" * 80)
    
    for name, expected in SCENARIOS.items():
        filepath = os.path.join(routes_dir, f"{name}.rou.xml")
        if not os.path.exists(filepath):
            print(f"{name:<20} | Missing File!")
            all_passed = False
            continue
            
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        we_count = sum(1 for v in root.findall('vehicle') if v.get('route') == 'route_we')
        ns_count = sum(1 for v in root.findall('vehicle') if v.get('route') == 'route_ns')
        
        status = "PASS" if we_count == expected['we'] and ns_count == expected['ns'] else "FAIL"
        if status == "FAIL":
            all_passed = False
            
        print(f"{name:<20} | {expected['we']:<12} | {we_count:<10} | {expected['ns']:<12} | {ns_count:<10} | {status}")
        
    return all_passed

def verify_net_file():
    print("\n--- Network Traffic Light Verification ---")
    filepath = os.path.join(WORKSPACE_DIR, "sumofiles", "Traci.net.xml")
    if not os.path.exists(filepath):
        print("Traci.net.xml is missing!")
        return False
        
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    tl_logic = root.find(".//tlLogic")
    if tl_logic is None:
        print("tlLogic element not found in Traci.net.xml")
        return False
        
    phases = tl_logic.findall("phase")
    if len(phases) < 4:
        print(f"Expected at least 4 phases, found {len(phases)}")
        return False
        
    p0 = phases[0].get('state') == 'GGrr'
    p1 = phases[1].get('state') == 'yyrr' and phases[1].get('duration') == '3'
    p2 = phases[2].get('state') == 'rrGG'
    p3 = phases[3].get('state') == 'rryy' and phases[3].get('duration') == '3'
    
    print(f"Phase 0 (WE Green 'GGrr'): {'PASS' if p0 else 'FAIL'}")
    print(f"Phase 1 (WE Yellow 3s 'yyrr'): {'PASS' if p1 else 'FAIL'}")
    print(f"Phase 2 (NS Green 'rrGG'): {'PASS' if p2 else 'FAIL'}")
    print(f"Phase 3 (NS Yellow 3s 'rryy'): {'PASS' if p3 else 'FAIL'}")
    
    return p0 and p1 and p2 and p3

def verify_sumocfg():
    print("\n--- sumocfg Path Resolution Verification ---")
    filepath = os.path.join(WORKSPACE_DIR, "src", "Traci.sumocfg")
    if not os.path.exists(filepath):
        print("Traci.sumocfg is missing!")
        return False
        
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    net_file = root.find(".//net-file")
    route_files = root.find(".//route-files")
    
    net_pass = net_file is not None and net_file.get('value') == '../sumofiles/Traci.net.xml'
    route_pass = route_files is not None and route_files.get('value') == '../sumofiles/routes/s3_heavy_asym_1200.rou.xml'
    
    print(f"net-file path ('../sumofiles/Traci.net.xml'): {'PASS' if net_pass else 'FAIL'}")
    print(f"route-files path ('../sumofiles/routes/s3_heavy_asym_1200.rou.xml'): {'PASS' if route_pass else 'FAIL'}")
    
    return net_pass and route_pass

if __name__ == "__main__":
    v1 = verify_scenarios()
    v2 = verify_net_file()
    v3 = verify_sumocfg()
    
    print("\n=======================================================")
    print("                STEP 1 COMPLIANCE REPORT               ")
    print("=======================================================")
    print(f"Scenario Verification:   {'[OK]' if v1 else '[FAILED]'}")
    print(f"Traffic Light Audit:     {'[OK]' if v2 else '[FAILED]'}")
    print(f"sumocfg Path Audit:      {'[OK]' if v3 else '[FAILED]'}")
    print("=======================================================")
    if v1 and v2 and v3:
        print("STATUS: 100% READINESS FOR STEP 2 (Dynamic Min-Max Calibration).")
    else:
        print("STATUS: FIX ISSUES BEFORE PROCEEDING.")
