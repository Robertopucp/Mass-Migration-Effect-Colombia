from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
import geopandas as gpd
from geopandas.tools import geocode
from tqdm import tqdm   #packages to mesuare time's loop
from shapely.geometry import Point, LineString, Polygon, MultiPoint

from pyproj import CRS
from matplotlib.lines import Line2D
import json
from shapely.ops import linemerge, unary_union, polygonize
from shapely.geometry import LineString, Polygon

import matplotlib.pyplot as plt 
import seaborn as sns

import warnings
warnings.filterwarnings('ignore') 

#Nightlights

from shapely.geometry import Polygon, MultiPolygon, shape, Point
import geemap, ee

try:
        ee.Initialize()
        
except Exception as e:
    
        ee.Authenticate()
        ee.Initialize()
        

#%%
   
# Function to convert shapefile to json format for Earth Engine

def shp_to_ee_fmt(geodf):
    data = json.loads(geodf.to_json())
    return data['features']

# Retriveing ee.file that contains the crops cover fraction from 2015 to 2019,
# with a spatial resolution of 100 m. 

coper = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global").filterDate('2015-01-01','2019-12-31').select('crops-coverfraction')


# Function collapses the cropland cover fraction to a single value for each geometry
# using the mean as the reduction method.

def reduce_mean(img, shapefile):
    
    try:
        mean = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=shapefile, scale=50, maxPixels= 1e9).get('crops-coverfraction') # adjust the scale to 30 m
        output = img.set('date', img.date().format()).set('crops_cover', mean)
        
    except:
        
        try:
            
            mean = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=shapefile, scale=100, maxPixels= 1e9).get('crops-coverfraction') # adjust the scale to 50 m
            output = img.set('date', img.date().format()).set('crops_cover', mean)
        
        except:
            
            try:
                
                mean = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=shapefile, scale=500, maxPixels= 1e9).get('crops-coverfraction') # adjust the scale to 100 m
                output = img.set('date', img.date().format()).set('crops_cover', mean)
            
            except:
                
                    
                mean = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=shapefile, scale=1000, maxPixels= 1e9).get('crops-coverfraction') # adjust the scale to 500 m
                output = img.set('date', img.date().format()).set('crops_cover', mean)

            
    
    
    return output

# Load the shapefile of Colombia's administrative divisions at level 2 (municipalities) using Geopandas.

colombia_amd2 = gpd.read_file(r"data\raw\shapefile\Colombia\col-administrative-divisions-shapefiles\col_admbnda_adm2_mgn_20200416.shp")


json_grids = shp_to_ee_fmt(colombia_amd2)    # Geopandas to Json file

total_data = {}

# Loop through each geometry in the json file, apply the reduce_mean function to calculate the mean cropland cover fraction for each geometry, and store the results in a DataFrame. Finally, concatenate all the DataFrames into a single DataFrame and save it as a Stata file.

for i in tqdm(range(len(json_grids))):

    geometry = ee.Geometry.MultiPolygon(json_grids[i]['geometry']['coordinates'])
    reduced_cities = coper.map(lambda x: reduce_mean(x,geometry))
    nested_list = reduced_cities.reduceColumns(ee.Reducer.toList(2), ['date','crops_cover']).values().get(0)
    df = pd.DataFrame(nested_list.getInfo(), columns=['date','crops_cover'])
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = pd.DatetimeIndex(df['date']).year
    df['adm2_pcode'] = json_grids[i]['properties']["ADM2_PCODE"]

    total_data[f'data{i}'] = df
    
data_f = pd.concat( total_data.values() ).reset_index( drop = True )

data_f.to_stata(fr"data\processed\Remote_sensing_data\Urban_crops_area\crops_cover.dta",
                write_index= False)