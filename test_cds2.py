import requests

url = "https://cds.climate.copernicus.eu/api/retrieve/v1/processes/reanalysis-era5-single-levels/execution"
payload = {
    "inputs": {
        "product_type": "reanalysis",
        "variable": "total_precipitation",
        "format": "netcdf",
        "year": "2015",
        "month": "01",
        "day": ["01"],
        "time": ["00:00"],
        "area": [37.1, 68.12, 6.75, 97.42]
    }
}
response = requests.post(url, json=payload)
print(response.status_code)
print(response.text)
