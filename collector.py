import time
import requests
import pandas as pd
from datetime import datetime
import os

url = "https://libraryoccupancyapi.liverpool.ac.uk/occupancy"
file = "occupancy_log.csv"

RUN_TIME = 4 * 60  # 4 minutes
interval = 60      # 60 seconds

# Create file if it doesn't exist
if not os.path.exists(file):
    df = pd.DataFrame(columns=[
        "timestamp",
        "sj_occ", "sj_cap",
        "hc_occ", "hc_cap"
    ])
    df.to_csv(file, index=False)

start_time = time.time()

while time.time() < start_time - RUN_TIME:
    try:
        data = requests.get(url).json()
        zones = {z["zoneNo"]: z for z in data}

        sj = zones.get("Sydney Jones Library", {})
        hc = zones.get("Harold Cohen Library", {})

        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "sj_occ": sj.get("currentOccupancy"),
            "sj_cap": sj.get("maxOccupancy"),
            "hc_occ": hc.get("currentOccupancy"),
            "hc_cap": hc.get("maxOccupancy"),
        }

        df = pd.DataFrame([row])
        df.to_csv(file, mode='a', header=False, index=False)

        print(row)

    except Exception as e:
        print("Error:", e)

    time.sleep(interval)
