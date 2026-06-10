import geocoder, geopy
from geopy.geocoders import Nominatim
import pandas as pd
import numpy as np   #  import googlemaps
import geopandas as gpd
from geopandas.tools import geocode
import multiprocessing as mp
from tqdm import tqdm   #packages to mesuare time's loop
from shapely.geometry import Point, LineString, Polygon, MultiPoint

from pyproj import CRS
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

import matplotlib.pyplot as plt 
import seaborn as sns

# pip install netCDF4 h5netcdf

import xarray as xr

import warnings
warnings.filterwarnings('ignore') 

#%%

# Load colombia country boundary

col_map = gpd.read_file(r"data\raw\1.bronce_raw_data\shapefile\Colombia\col-administrative-divisions-shapefiles\col_admbnda_adm0_mgn_itos_20200416.shp")

# Colombia administrative division level 2 (municipality)

colombia_amd2 = gpd.read_file(r"data\raw\1.bronce_raw_data\shapefile\Colombia\col-administrative-divisions-shapefiles\col_admbnda_adm2_mgn_20200416.shp")


## 1.0 Loop for computing the average CO2 emissions per municipality

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\1.bronce_raw_data\Remote_sensing_data\Pollution\TOTALS_emi_nc\EDGAR_2024_GHG_CO2_{year}_TOTALS_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    # GPS coordinates of CO2 pollution points
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    # Set data to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    # Projecting to coordinate system (WGS84: EPSG:4326)
    gdf.set_crs(epsg=4326, inplace=True)
    
    # Spatial merge GPS CO2 emmission that fall within colombia's boundary and then merge with municipality boundary to compute the average CO2 emission per municipality
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    # Collapsing of CO2 emissions per municipality
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    # Save the data for each year in a dictionary
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group

# Append all data together
    
data_collapse = pd.concat(dict_all_data.values(), axis =0)

data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_co2_emissions.dta",
                                 write_index =False)

## 2.0 CO2 emissions per type of activity

# - Energy Building
# - Combustion manufacturing
# - Agricultural soil
# - fuel explotation
# - oil refinery and transformation
# - road transportation
# - iron & steel production


## 2.1 Energy Building

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\Remote_sensing_data\Pollution\RCO_emi_nc_co2_energy building\EDGAR_2024_GHG_CO2_{year}_RCO_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    gdf.set_crs(epsg=4326, inplace=True)
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group
    
data_collapse = pd.concat(dict_all_data.values(), axis =0)

data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_energy_building_co2_emissions.dta",
                                 write_index =False)

## 2.2 Combustion for manufacturing

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\Remote_sensing_data\Pollution\IND_emi_nc_co2_combustion manufacturing\EDGAR_2024_GHG_CO2_{year}_IND_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    gdf.set_crs(epsg=4326, inplace=True)
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group
    
data_collapse = pd.concat(dict_all_data.values(), axis =0)
data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_manufactoring_co2_emissions.dta",
                                 write_index =False)

## 2.3 Agricultural Soil

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\Remote_sensing_data\Pollution\AGS_emi_nc_co2 agricultural soil\EDGAR_2024_GHG_CO2_{year}_AGS_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    gdf.set_crs(epsg=4326, inplace=True)
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group
    
data_collapse = pd.concat(dict_all_data.values(),
                          axis =0)
data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_agricultural_soil_co2_emissions.dta",
                                 write_index =False)

## 2.4 Fuel explotation

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\Remote_sensing_data\Pollution\PRO_FFF_emi_nc_fuel explotation\EDGAR_2024_GHG_CO2_{year}_PRO_FFF_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    gdf.set_crs(epsg=4326, inplace=True)
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group
    
data_collapse = pd.concat(dict_all_data.values(), axis =0)

data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_fuel_explotation_co2_emissions.dta",
                                 write_index =False)

## 2.5 oil refinery 

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\Remote_sensing_data\Pollution\REF_TRF_emi_nc_co2_oil refinery and transformation\EDGAR_2024_GHG_CO2_{year}_REF_TRF_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    gdf.set_crs(epsg=4326, inplace=True)
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group
    
data_collapse = pd.concat(dict_all_data.values(), axis =0)
data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_oil_refinery_co2_emissions.dta",
                                 write_index =False)

## 2.6 Road transportation

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\Remote_sensing_data\Pollution\TRO_emi_nc_co2_road transportation\EDGAR_2024_GHG_CO2_{year}_TRO_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    gdf.set_crs(epsg=4326, inplace=True)
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group
    
data_collapse = pd.concat(dict_all_data.values(), axis =0)
data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_road_transportation_co2_emissions.dta",
                                 write_index =False)

## 2.7 Iron and steel production

dict_all_data={}

for year in tqdm(range(2000,2024)):
    
    ds = xr.open_dataset(fr"data\raw\Remote_sensing_data\Pollution\IRO_emi_nc_co2_iron and steel\EDGAR_2024_GHG_CO2_{year}_IRO_emi.nc",
                     engine="rasterio")
    
    df = ds['emissions'].to_dataframe().reset_index()
    
    df['geometry'] = df.apply(lambda row: Point(row['x'], row['y']), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    gdf.set_crs(epsg=4326, inplace=True)
    
    co2_emission_colombia = gpd.sjoin(gdf, col_map[['geometry']], 
    how = 'inner', op = "intersects")
    
    co2_emission_colombia_adm2 = gpd.sjoin(colombia_amd2, co2_emission_colombia[['geometry','emissions']], 
    how = 'left', op = "intersects")
    
    co2_emission_colombia_adm2_group = co2_emission_colombia_adm2.groupby('ADM2_PCODE', as_index= False)['emissions'].mean()
    co2_emission_colombia_adm2_group['year']=year
    
    dict_all_data[f'data_mun_{year}']=co2_emission_colombia_adm2_group
    
    
data_collapse = pd.concat(dict_all_data.values(), 
                          axis =0)

data_collapse.to_stata(r"data\processed\Remote_sensing_data\Pollution\Colombia_steel_production_co2_emissions.dta",
                                 write_index =False)


