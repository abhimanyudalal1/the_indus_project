import ee
import geopandas
import pandas

i_date='1999-01-01'
m_date='2012-06-06'
f_date='2025-12-12'

dataset1 = ee.ImageCollection('NASA/GPM_L3/IMERG_V07').filterDate(i_date, m_date)
dataset2 = ee.ImageCollection('NASA/GPM_L3/IMERG_V07').filterDate(m_date, f_date)

print(f"Date range: {i_date} to {f_date}")

def calc_monthly_precipitation(image):
    date=image.date().format('YYYY-MM-dd')

    mean_val = ee.reduceRegion(
       reducer = ee.Reducer.mean(),
       geometry = ee_object.geometry()
       scale = 11132
    )