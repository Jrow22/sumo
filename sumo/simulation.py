import traci
import sumolib
import random
import xml.etree.ElementTree as ET
import os
import subprocess
from supabase import create_client, Client
import requests
from datetime import datetime, timedelta, timezone

url: str = "https://mgvaztrwyspjhzqohbqt.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ndmF6dHJ3eXNwamh6cW9oYnF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA5NDM3NzksImV4cCI6MjA0NjUxOTc3OX0.Qhr6h3U37-KuJp7BcxWRrTbjGgsf8h14wlLlu6yj3DM"
supabase: Client = create_client(url, key)

SUMO_HOME = "/Library/Frameworks/EclipseSUMO.framework/Versions/1.23.1/EclipseSUMO"
os.environ["SUMO_HOME"] = SUMO_HOME

class Simulation:
    def __init__(self, net_file: str, options: dict):
        self.net = sumolib.net.readNet(net_file)
        self.destinations = self.get_crimes()
        self.SIMULATION_TIME = 6000
        self.options = options
        self.traci = traci

    def get_valid_edge(self, lon: float, lat: float):
        x, y = self.net.convertLonLat2XY(lon, lat)
        nearby_edges = self.net.getNeighboringEdges(x, y, 500)  # 500m radius
        for lane, _ in nearby_edges:
            if lane.allows("passenger"):
                return lane.getID()
        raise Exception(f"No valid edge found near ({lon}, {lat})")
    
    def generate_trips_file(self,trips, filename="generated_trips.trips.xml"):
        root = ET.Element("routes")

        ET.SubElement(
            root, "vType",
            id="car",
            accel="2.6",
            decel="4.5",
            length="5",
            maxSpeed="35"
        )

        sorted_trips = sorted(trips, key=lambda x: float(x["depart"]))

        for trip in sorted_trips:
            trip_element = ET.SubElement(root, "trip",
                        id=trip["id"],
                        depart=str(trip["depart"]),
                        **{
                            "from": trip["from_edge"]
                        },
                        to=trip["to_edge"],
                        type="car"
            )

            for key, val in trip["properties"].items():
                ET.SubElement(trip_element, "param", key=key, value=str(val))

        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)
        return filename

    def get_valid_starting_edge(self):
        """Get a valid starting edge near police stations"""
        stations = [
            (-87.68954611946626, 41.9400173076878),
            (-87.65116121064099, 41.94775059922128)
        ]
        lon, lat = random.choice(stations)
        return self.get_valid_edge(lon, lat)
        

    def create_routes(self):
        trips = []
        from_edge = self.get_valid_starting_edge()
        for crime in self.destinations:
            print(crime)
            crime_edge, _, _ = traci.simulation.convertRoad(
                    float(crime["longitude"]), 
                    float(crime["latitude"]), 
                    isGeo=True
                )
            print(crime_edge)
            if not crime_edge.startswith(':'):
                trip = {
                    "id": f"police{len(trips)}",
                    "depart": random.uniform(0, self.SIMULATION_TIME),
                    "from_edge": from_edge,
                    "to_edge": crime_edge,
                    "properties": crime
                }
                trips.append(trip)
                
        return trips
    
    def run_step(self):
        traci.simulationStep()
        positions = {"police": [], "vehicles": []}
        for veh_id in traci.vehicle.getIDList():
            x, y = traci.vehicle.getPosition(veh_id)
            lon, lat = traci.simulation.convertGeo(x, y)
            angle = traci.vehicle.getAngle(veh_id)
            position_data = {
                "id": veh_id,
                "lat": lat,
                "lon": lon,
                "angle": angle
            }
            if veh_id.startswith("police"):
                position_data["primary_type"] = traci.vehicle.getParameter(veh_id, "primary_type")
                position_data["description"] = traci.vehicle.getParameter(veh_id, "description")
                position_data["block"] = traci.vehicle.getParameter(veh_id, "block")
                position_data["arrest"] = traci.vehicle.getParameter(veh_id, "arrest")
                positions["police"].append(position_data)
            else:
                positions["vehicles"].append(position_data)
        return positions
    
    def run_simulation(self):
        for step in range(self.SIMULATION_TIME):
            self.run_step()

    def generate_random_trips(self,
    net_file: str,
    output_file: str = "random_trips.trips.xml",
    end_time: int = 6000,
    depart_period: float = 5.0,
    sumo_tools_path: str = None
        ):
        if sumo_tools_path is None:
            # Try to get from SUMO_HOME env variable
            sumo_tools_path = os.path.join(os.environ.get("SUMO_HOME", ""), "share/sumo/tools")

        random_trips_script = os.path.join(sumo_tools_path, "randomTrips.py")

        if not os.path.isfile(random_trips_script):
            raise FileNotFoundError(f"Could not find randomTrips.py at {random_trips_script}")

        cmd = [
            "python",
            random_trips_script,
            "-n", net_file,
            "-o", output_file,
            "-e", str(end_time),
            "-p", str(depart_period),
        ]

        print("Running command:", " ".join(cmd))

        # Run the command and wait for it to finish
        subprocess.run(cmd, check=True)
        print(f"Random trips file generated: {output_file}")

    def start_simulation(self):
        self.traci.start(self.options)
        #self.traci.connect(8813)
    
    def stop_simulation(self):
        self.traci.close()  

    def get_crimes(self):
        now = datetime.now(timezone.utc)
        nine_days_ago = now - timedelta(days=14)
        nine_days_str = nine_days_ago.strftime('%Y-%m-%dT%H:%M:%S')

        # Coordinates for within_box() spatial filter
        north = 41.94775059922128
        east = -87.65116121064099
        south = 41.9400173076878
        west = -87.68954611946626

        # Build SOQL WHERE clause
        where_clause = (
            f"within_box(location, {north}, {east}, {south}, {west}) "
            f"AND date >= '{nine_days_str}'"
        )

        # API endpoint
        base_url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"

        # Query parameters
        params = {
            "$where": where_clause,
            "$order": "date DESC",
            "$limit": 1000  # adjust as needed
        }

        # Make the request
        response = requests.get(base_url, params=params)
        data = response.json()
        return data