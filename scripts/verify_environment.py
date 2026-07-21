import os
import xml.etree.ElementTree as ET
from pathlib import Path

def main():
    base_dir = Path(r"C:\VSCODE\CISInternship_Implement")
    net_path = base_dir / "sumofiles" / "Traci.net.xml"
    sumocfg_path = base_dir / "src" / "Traci.sumocfg"
    routes_dir = base_dir / "sumofiles" / "routes"

    print("="*60)
    print("STEP 1: MULTI-SCENARIO ENVIRONMENT VERIFICATION AUDIT")
    print("="*60)

    all_passed = True

    scenarios = [
        ("s1_low_200.rou.xml", 150, 50),
        ("s2_medium_600.rou.xml", 450, 150),
        ("s3_heavy_asym_1200.rou.xml", 900, 300),
        ("s4_heavy_sym_1200.rou.xml", 600, 600),
        ("s5_peak_1800.rou.xml", 1200, 600)
    ]

    # 1. Route Flow Verification
    print("\n[1] Route Flow Verification (sumofiles/routes/)")
    print(f"{'Scenario':<30} | {'Expected (WE/NS)':<20} | {'Actual (WE/NS)':<20} | {'Status'}")
    print("-" * 80)
    for filename, exp_we, exp_ns in scenarios:
        filepath = routes_dir / filename
        if not filepath.exists():
            print(f"{filename:<30} | {exp_we}/{exp_ns:<19} | {'NOT FOUND':<20} | [FAIL]")
            all_passed = False
            continue
            
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        total_we = 0
        total_ns = 0
        for vehicle in root.findall('vehicle'):
            route = vehicle.get('route', '')
            vid = vehicle.get('id', '').lower()
            if 'we' in route.lower() or vid.startswith('we'):
                total_we += 1
            elif 'ns' in route.lower() or vid.startswith('ns'):
                total_ns += 1
                
        if total_we == exp_we and total_ns == exp_ns:
            status = "[PASS]"
        else:
            status = "[FAIL]"
            all_passed = False
            
        print(f"{filename:<30} | {exp_we}/{exp_ns:<19} | {f'{total_we}/{total_ns}':<19} | {status}")

    # 2. Network Audit
    print("\n[2] Network & Phase Audit (Traci.net.xml)")
    if not net_path.exists():
        print(f"  [ERROR] File not found: {net_path}")
        all_passed = False
    else:
        tree = ET.parse(net_path)
        root = tree.getroot()
        tl_logics = root.findall('tlLogic')
        for tl in tl_logics:
            phases = tl.findall('phase')
            if len(phases) == 4 and float(phases[1].get('duration')) == 3.0 and 'y' in phases[1].get('state').lower() and \
               float(phases[3].get('duration')) == 3.0 and 'y' in phases[3].get('state').lower():
                print("    [PASS] Phase structure matches Phase 0-3 sequence with 3s yellows.")
            else:
                print("    [FAIL] Phase structure is invalid.")
                all_passed = False

    # 3. Configuration Audit
    print("\n[3] Configuration Verification (Traci.sumocfg)")
    if not sumocfg_path.exists():
        print(f"  [ERROR] File not found: {sumocfg_path}")
        all_passed = False
    else:
        tree = ET.parse(sumocfg_path)
        root = tree.getroot()
        input_tag = root.find('input')
        if input_tag is not None:
            net_file = input_tag.find('net-file')
            route_files = input_tag.find('route-files')
            
            nf_val = net_file.get('value').replace('\\', '/') if net_file is not None else ""
            rf_val = route_files.get('value').replace('\\', '/') if route_files is not None else ""
            
            if nf_val == '../sumofiles/Traci.net.xml':
                print("  - net-file: [PASS]")
            else:
                print(f"  - net-file: [FAIL] Got '{nf_val}'")
                all_passed = False
                
            if rf_val == '../sumofiles/routes/s3_heavy_asym_1200.rou.xml':
                print("  - route-files: [PASS]")
            else:
                print(f"  - route-files: [FAIL] Got '{rf_val}'")
                all_passed = False
        else:
            print("  [FAIL] <input> tag not found.")
            all_passed = False

    print("\n" + "="*60)
    print("STEP 1 COMPLIANCE REPORT")
    print("="*60)
    if all_passed:
        print("STATUS: COMPLIANT [100%]")
        print("The 5-scenario setup is verified and fully compliant.")
        print("Ready for STEP 2 (Dynamic Min-Max Calibration).")
    else:
        print("STATUS: NON-COMPLIANT")
        print("Please fix the reported errors before proceeding to training.")

if __name__ == '__main__':
    main()
