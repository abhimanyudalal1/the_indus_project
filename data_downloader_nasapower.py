import requests
import pandas as pd
import time

years=2025
parameters=["EVPTRNS", "TSURF", "T2M_RANGE", "PRECSNO", "IMERG_PRECTOT"]
regions=[
    {"lat_min": 23, "lat_max": 33, "lon_min": 66, "lon_max": 75},
    {"lat_min": 23, "lat_max": 33, "lon_min": 75, "lon_max": 83},
    {"lat_min": 33, "lat_max": 38, "lon_min": 66, "lon_max": 75},
    {"lat_min": 33, "lat_max": 38, "lon_min": 75, "lon_max": 83}
]

base_url="https://power.larc.nasa.gov/api/temporal/daily/regional"

#gotta make this- https://power.larc.nasa.gov/api/temporal/daily/point?start=20000101&end=20260101&latitude=30&longitude=73&community=re
# &parameters=TSURF%2CT2M_RANGE%2CPRECSNO%2CIMERG_PRECTOT&format=json&units=metric&user=abhimanyu&header=true&time-standard=lst
#|for regional
def fetch_data():
        for param in parameters:
            for i,reg in enumerate(regions):
                params={
                    "start": f"{years}0101",
                    "end": f"{years}1231",
                    "latitude-min": reg["lat_min"],
                    "latitude-max": reg["lat_max"],
                    "longitude-min": reg["lon_min"],
                    "longitude-max": reg["lon_max"],
                    "parameters": param,
                    "community": "AG",
                    "format": "JSON",
                    "units": "metric",
                    "user": "abhimanyu",
                    "header": "true",
                    "time-standard": "lst"

                }
                response = requests.get(base_url, params=params)
                if response.status_code == 200:
                    with open(f"indus_{years}_{param}_tile{i}.json", "w") as f:
                        f.write(response.text)
                    print(f"Saved: {years}-{param}- Tile {i}")
                else: 
                    print(f"error{response.status_code} for {years} {param}")

                time.sleep(2)

fetch_data()

