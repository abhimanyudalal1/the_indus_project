import ee
import requests

ee.Initialize(project='test') # We might not have project setup, let's see.

# Define area
geom = ee.Geometry.Rectangle([73.1, 19.5, 75.0, 21.0])

# Just test getting a download URL for one day
col = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterDate('1980-01-01', '1980-01-02').select('total_precipitation')
img = col.sum() # daily sum

url = img.getDownloadURL({
    'region': geom,
    'scale': 11132, # approx 0.1 deg
    'format': 'GEO_TIFF'
})
print("URL:", url)
