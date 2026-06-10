import geocoder, geopy
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np
import math
import geopandas as gpd
from geopandas.tools import geocode
import re
import multiprocessing as mp
from tqdm import tqdm   #packages to mesuare time's loop
from shapely.geometry import Point, LineString, Polygon, MultiPoint
import os 
import rasterio
import time

from pyproj import CRS
import matplotlib.patches as mpatches
from tqdm import tqdm
import swifter # parallel procesing 
from matplotlib.lines import Line2D
import json
from shapely.ops import linemerge, unary_union, polygonize
from shapely.geometry import LineString, Polygon

import matplotlib.pyplot as plt 
import os
import seaborn as sns
from shapely.geometry import box

import warnings
warnings.filterwarnings('ignore') 

from rasterio.mask import mask

#%%

## 1.0 Municipio Night Light
shapefile = gpd.read_file(fr"data\raw\shapefile\Colombia\col-administrative-divisions-shapefiles\col_admbnda_adm2_mgn_20200416.shp",
                    crs = "EPSG:4326")

# centroid of each geometry and extract longitude and latitude

shapefile['centroid']=shapefile['geometry'].centroid

shapefile['longitude']=shapefile['centroid'].x

shapefile['latitude']=shapefile['centroid'].y

del shapefile['centroid']

shapefile.columns = shapefile.columns.str.lower()


# Loop through the years and compute the mean of night light data across municipalities, 
# then save the results in a .dta file for each year.

for year in tqdm(range(1992,2022)):
    
    inv_hipe_light = []
    raw_mean_nightlight = []
    
    if year < 2014:   
            
        for i in range(shapefile.shape[0]):
            
            with rasterio.open(fr'data\raw\Nightlight\9828827\Harmonized_DN_NTL_{year}_calDMSP.tif') as src: 

                # Extract the first geometry from the shapefile as the clipping geometry

                clip_geometry = shapefile.geometry.iloc[i]

                # Convert the clipping geometry to a list of geometries
                shapes = [clip_geometry]

                # Clip the raster using the clipping geometry
                clipped_raster, transform = mask(src, shapes, crop=True)

                # Update the metadata of the clipped raster
                out_meta = src.meta

                out_meta.update({'height': clipped_raster.shape[1],
                                'width': clipped_raster.shape[2],
                                'transform': transform})

                # Save the clipped raster to a new file
                with rasterio.open(fr'data\raw\Nightlight\clipped_raster_{i}_{year}_muni.tif', 'w', **out_meta) as dst:
                    
                    dst.write(clipped_raster)
                
                
                # Open rater 
                with rasterio.open(fr'data\raw\Nightlight\clipped_raster_{i}_{year}_muni.tif') as src:
                    
                    data = src.read()

                # Inverse hyperbolic sine transformation to handle zero values 
                # and reduce the influence of extreme values
                
                array = data[0].reshape(-1)
                inv_hyper = np.mean(np.log(array + (array**2+1)**0.5)) # inverse hyperbolic scale
                raw_mean = np.mean(array)
                inv_hipe_light.append(inv_hyper)
                raw_mean_nightlight.append(raw_mean)
                
                os.remove(fr'data\raw\Nightlight\clipped_raster_{i}_{year}_muni.tif')

        df = shapefile[["adm0_es","adm0_pcode","adm1_es","adm1_pcode","adm2_es","adm2_pcode",'longitude','latitude']]
        df['year'] = year
        df['inv_hipe_mean'] = inv_hipe_light
        df['raw_mean'] = raw_mean_nightlight

        
        df.to_stata(fr"data\processed\Nightlight\municipio_col\col_light_night_{year}.dta",
                    write_index = False)
        
    else:
        
        for i in range(shapefile.shape[0]):
            
            with rasterio.open(fr'data\raw\Nightlight\9828827\Harmonized_DN_NTL_{year}_simVIIRS.tif') as src: 

                # Extract the first geometry from the shapefile as the clipping geometry

                clip_geometry = shapefile.geometry.iloc[i]
                
                # Convert the clipping geometry to a list of geometries
                shapes = [clip_geometry]

                # Clip the raster using the clipping geometry
                clipped_raster, transform = mask(src, shapes, crop=True)

                # Update the metadata of the clipped raster
                out_meta = src.meta

                out_meta.update({'height': clipped_raster.shape[1],
                                'width': clipped_raster.shape[2],
                                'transform': transform})

                # Save the clipped raster to a new file
                with rasterio.open(fr'data\raw\Nightlight\clipped_raster_{i}_{year}_muni.tif', 'w', **out_meta) as dst:
                    dst.write(clipped_raster)
                    
                
                # Open rater 
                with rasterio.open(fr'data\raw\Nightlight\clipped_raster_{i}_{year}_muni.tif') as src:
                    data = src.read()

                array = data[0].reshape(-1) 
                inv_hyper = np.mean(np.log(array + (array**2+1)**0.5)) # inverse hyperbolic sine scale
                inv_hipe_light.append(inv_hyper)
                
                raw_mean = np.mean(array)
                raw_mean_nightlight.append(raw_mean)
                
                os.remove(fr'data\raw\Nightlight\clipped_raster_{i}_{year}_muni.tif')

        df = shapefile[["adm0_es","adm0_pcode","adm1_es","adm1_pcode","adm2_es","adm2_pcode",'longitude','latitude']]
        df['year'] = year
        df['inv_hipe_mean'] = inv_hipe_light
        df['raw_mean'] = raw_mean_nightlight

        df.to_stata(fr"data\processed\Nightlight\municipio_col\col_light_night_{year}.dta",
                    write_index = False)





