from simulation import Simulation  # Assuming your class is in simulation.py
import time
import os
import redis
import json
import gzip
from datetime import datetime, timedelta

# Set SUMO_HOME to a sensible default if not already defined
default_sumo_home = "/usr/share/sumo"
os.environ["SUMO_HOME"] = default_sumo_home

# Set route file depending on environment
ROUTE_FILE = "generated_trips.trips.xml"

# 🔌 Connect to Redis
redis_url = "redis://redis:6379"
r = redis.from_url(redis_url, decode_responses=True)
            
'''sumo_process = subprocess.Popen([
    "sumo",
    "-c", "chicago.sumocfg",
    "--start",
    "--ignore-route-errors",
    "--remote-port", "8813"
])
'''
def route_file_old():
    if not os.path.exists(ROUTE_FILE):
        return True
    modified = datetime.fromtimestamp(os.path.getmtime(ROUTE_FILE))
    return datetime.now() - modified > timedelta(hours=ROUTE_GEN_INTERVAL_HOURS)

def compress_json_gzip(data):
    json_string = json.dumps(data)
    json_bytes = json_string.encode('utf-8')
    return gzip.compress(json_bytes, compresslevel=9)

def run_simulation():
    # Path to your files
    net_file = 'chicago_n.net.xml'
    config_file = "chicago.sumocfg"
    
    # Start SUMO GUI
    sumo_cmd = ["sumo", "-c", config_file, "--start", "--ignore-route-errors", "--verbose"]

    sim = Simulation(net_file, sumo_cmd)

    try:
        while True:
            sim.start_simulation()
            while True:
                sim_state = r.get("sim_control")
                if sim_state != "start":
                    print("No WebSocket clients connected — pausing simulation")
                    time.sleep(1)
                    continue

                if sim.traci.simulation.getMinExpectedNumber() <= 0:
                    print("Simulation finished")
                    break
                
                positions = sim.run_step()
                compressed_data = compress_json_gzip(positions)
                r.publish("positions", compressed_data)
                time.sleep(0.1)
            sim.stop_simulation()
    except Exception as e:
        print("Simulation failed:", e)
        sim.stop_simulation()
        return

if __name__ == "__main__":
    run_simulation()