import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import os
import argparse

def generate_routes(output_file, episode_seed, total_time=1000.0, we_count=900, ns_count=300):
    """
    Dynamically writes a seed-based SUMO route file (.rou.xml).
    """
    # 4. Reproducibility: Accept an episode_seed parameter that explicitly sets the random seed
    random.seed(episode_seed)

    routes = ET.Element("routes")
    routes.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    routes.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/routes_file.xsd")

    # Define vehicle type
    vtype = ET.SubElement(routes, "vType")
    vtype.set("id", "car")
    vtype.set("maxSpeed", "13.89")
    vtype.set("length", "4.7")

    # Define routes explicitly for the vehicles
    # West-East: From edge "E0" to "E0.58"
    route_we = ET.SubElement(routes, "route")
    route_we.set("id", "route_we")
    route_we.set("edges", "E0 E0.58")

    # North-South: From edge "E1" to "E2"
    route_ns = ET.SubElement(routes, "route")
    route_ns.set("id", "route_ns")
    route_ns.set("edges", "E1 E2")

    vehicles = []

    # 3. Micro-Variance: individual <vehicle> components with randomized departure times via uniform distribution
    # Generate West-East vehicles
    for i in range(we_count):
        depart = random.uniform(0, total_time)
        vehicles.append({
            "id": f"we_{i}",
            "route": "route_we",
            "depart": depart
        })

    # Generate North-South vehicles
    for i in range(ns_count):
        depart = random.uniform(0, total_time)
        vehicles.append({
            "id": f"ns_{i}",
            "route": "route_ns",
            "depart": depart
        })

    # Sort sequentially by departure time
    vehicles.sort(key=lambda x: x["depart"])

    # Create individual <vehicle> xml elements
    for veh in vehicles:
        vehicle = ET.SubElement(routes, "vehicle")
        vehicle.set("id", veh["id"])
        vehicle.set("type", "car")
        vehicle.set("route", veh["route"])
        vehicle.set("depart", f"{veh['depart']:.2f}")
        vehicle.set("departLane", "0")

    # Format the XML output
    xmlstr = minidom.parseString(ET.tostring(routes)).toprettyxml(indent="    ")
    
    with open(output_file, "w") as f:
        # Write XML header manually if preferred, but minidom toprettyxml adds it: 
        # <?xml version="1.0" ?>
        f.write(xmlstr)

    print(f"Successfully generated {we_count + ns_count} vehicles in {output_file} with seed {episode_seed}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SUMO route file dynamically for training.")
    parser.add_argument("--output", type=str, default="Traci.rou.xml", help="Output route XML file name/path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation")
    args = parser.parse_args()

    # Generate route file
    generate_routes(args.output, args.seed)
