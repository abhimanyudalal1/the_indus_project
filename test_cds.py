import cdsapi

client = cdsapi.Client(quiet=True, wait_until_complete=True)

request = {
    "product_type": "reanalysis",
    "variable": "total_precipitation",
    "daily_statistic": "daily_sum",
    "year": "2015",
    "month": "01",
    "day": ["01"],
    "time_zone": "utc+05:30",
    "area": [37.1, 68.12, 6.75, 97.42],
    "frequency": "1_hourly",
}

try:
    client.retrieve("derived-era5-single-levels-daily-statistics", request, "test.nc")
    print("Success")
except Exception as e:
    print("ERROR:", e)
