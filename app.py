import streamlit as st
from streamlit.components.v1 import html
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from streamlit_extras.stylable_container import stylable_container 
#import leafmap.foliumap as leafmap

import folium
from folium.plugins import BeautifyIcon

import json
import pandas as pd
# the command below causes segmentation fault on local computer
#from st_aggrid import AgGrid, GridOptionsBuilder

import altair as alt
from vega_datasets import data

#from streamlit_folium import folium_static, st_folium

import geopandas as gpd

from shapely.geometry import shape, MultiPolygon, MultiLineString

import csv 

# Initialize the list in st.session_state if it doesn't exist
if 'selected_county_list' not in st.session_state:
    st.session_state.selected_county_list = []
if 'selected_data_list' not in st.session_state:
    st.session_state.selected_data_list = []

# for Main2()
if 'selected_rows' not in st.session_state:
    st.session_state.selected_rows = None
    
if 'cluster_summary_df' not in st.session_state:
    st.session_state.cluster_summary_df = pd.DataFrame({})
    
if 'associated_projects_df' not in st.session_state:
    st.session_state.associated_projects_df = pd.DataFrame({})
    
if 'w1' not in st.session_state:
    st.session_state.w1 = 1
    st.session_state.w2 = 1
    st.session_state.w3 = 1
    st.session_state.w4 = 1



from clusterPage import main2

@st.cache_data
def load_basemap() :
    basemap = alt.topo_feature(data.us_10m.url, 'states')
    return basemap 

##@st.cache_data
##def load_excel(path, sheetname):
##    data = pd.read_excel(path, sheetname)
##    return data

@st.cache_data
def load_geojson(file_path):
    with open(file_path, 'r') as file:
        geojson_data = json.load(file)
    return geojson_data

@st.cache_data
def load_csv(path):
    data = pd.read_csv(path)
    return data

##@st.cache_data
##def load_transmission_lines(file_path):
##    # transmission lines geojson
##    with open(file_path, 'r') as file:
##        trans_lines = json.load(file)
##    return trans_lines    

@st.cache_data
def extract_geojson_by_county(county, in_geojson) :
    # create a new GeoJSON structure for the extracted county
    extracted_geojson = {
        "type": "FeatureCollection",
        "name": f"{county}_Boundary",
        "crs": in_geojson["crs"],
        "features": []
    }    
    for feature in in_geojson['features'] :
        if feature['properties']['CountyName'] == county :
            extracted_geojson["features"].append(feature)
            break
        
    return extracted_geojson

@st.cache_data
def get_county_centroid(in_county):
    # Using Shapely to create a geometry from the GeoJSON geometry
    geom = shape(in_county['features'][0]['geometry'])
    # If the geometry is a MultiPolygon, calculate the centroid of the largest polygon by area
    if isinstance(geom, MultiPolygon):
        # Corrected handling of MultiPolygon
        largest_area = 0
        largest_polygon = None
        for polygon in geom.geoms:
            if polygon.area > largest_area:
                largest_area = polygon.area
                largest_polygon = polygon
        centroid = largest_polygon.centroid if largest_polygon else None
    else:
        centroid = geom.centroid
    return centroid.x, centroid.y

@st.cache_data    
def extract_lines_within_county(lines_geojson, county_geojson):
    # get county shape
    county_shape = shape(county_geojson['features'][0]['geometry'])

    within_lines = []
    for feature in lines_geojson['features'] :
        line_shape = shape(feature['geometry'])
        #if line_shape.within(county_shape) :
        if line_shape.intersects(county_shape) :
            within_lines.append(feature)

    # create a new GeoJSON structure for within lines
    within_lines_geojson = {
        "type": "FeatureCollection",
        "crs": lines_geojson["crs"],
        "features": within_lines
    }    
    return within_lines_geojson

@st.cache_data    
def extract_points_within_county(points_geojson, county_geojson):
    # get county shape
    county_shape = shape(county_geojson['features'][0]['geometry'])

    within_points = []
    for feature in points_geojson['features'] :
        point_shape = shape(feature['geometry'])
        if point_shape.within(county_shape) :
            within_points.append(feature)

    # create a new GeoJSON structure for within points
    within_points_geojson = {
        "type": "FeatureCollection",
        "crs": points_geojson["crs"],
        "features": within_points
    }
    
    return within_points_geojson

def is_valid_coordinate(lat, lon):
    """Check if the provided latitude and longitude values are valid."""
    return -90 <= lat <= 90 and -180 <= lon <= 180

def extract_retired_plants(geojson_data) :
    # Filter features where "Retired_Plant" equals 1
    filtered_features = [
        feature for feature in geojson_data["features"] if feature["properties"]["Retired_Plant"] == 1
    ]

    # Create a new GeoJSON structure with the filtered features
    filtered_geojson_data = {
        "type": "FeatureCollection",
        "crs": geojson_data["crs"],
        "features": filtered_features,
    }

    return filtered_geojson_data

# convert shape file to geojson
def save_shp_to_geojson(shp_file):
    # convert to geojson
    gdf = gpd.read_file(shp_file)
    gdf.to_crs('EPSG:4326', inplace=True)
    json_file = shp_file.replace('.shp','.geojson')
    gdf.to_file(json_file, driver='GeoJSON')

# save geojson to csv / no longer in use 
def geojson_to_csv(geojson_data, csv_file) :
    # get headers from geojson
    headers_from_properties = list(geojson_data["features"][0]["properties"].keys())
    # Add point coordinates to the headers
    headers = ['latitude','longitude'] + headers_from_properties
    
    # Open a new CSV file
    with open(csv_file, mode='w', newline='') as csv_file:
        # Create a CSV writer object
        csv_writer = csv.writer(csv_file)
        
        # Write the header row based on the properties you want to include
        csv_writer.writerow(headers)
        
        # Loop through each feature in your GeoJSON data
        for feature in geojson_data['features']:
            # Extract the coordinates (assuming Point geometry for simplicity)
            longitude, latitude = feature['geometry']['coordinates']
            
            # Extract the properties you're interested in
            property_list = [feature['properties'][iprop] for iprop in headers_from_properties]
            
            # Write a row for this feature
            csv_writer.writerow([latitude, longitude]+property_list)    
    return

# convert pd df to geojson
def df_to_geojson(df, crs, lat_col='GIS Lat', lon_col='GIS Long') :
    # Define the base structure of the GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "crs": crs,
        "features": []
    }
    
    # Iterate over DataFrame rows to populate the GeoJSON Features
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row[lon_col], row[lat_col]]
            },
            "properties": row.drop([lon_col, lat_col]).to_dict()
        }
        geojson['features'].append(feature)    
    return geojson 

import math
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    # Difference in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance

# find the nearest transmission line
def find_nearest_line(queue_df, lines_geojson, all_county_geojson) :
    lon_col = 'GIS Long'
    lat_col = 'GIS Lat'
    county_col = 'County'
    # create new columns in dataframe
    queue_df['Line_Name'] = 'None'
    queue_df['Min_Dist'] = 0
    queue_df['Cap_MW'] = 0
    queue_df['Load_Pct'] = 0
    queue_df['Remain_MW'] = 0

    # get unique county list
    county_list = list(queue_df[county_col].unique())
    #county_list.remove('tecate baja california mexico')
    
    st.write('total number of counties: '+ str(len(county_list)))
    st.write(county_list)
    
    # iterate for each county
    for icounty in county_list :
        # make sure the string is consistent with CA county names
        county = icounty.title()
        st.write(county)
        # select county boundary 
        county_data = extract_geojson_by_county(county, all_county_geojson)
        # select transmission lines within county boundary
        lines_data = extract_lines_within_county(lines_geojson, county_data)
        
        # iterate each row in data frame
        for index, row in queue_df.iterrows():
            # only update rows for icounty 
            if row[county_col] == icounty :
                # get lat and lon of the row
                q_lat = row[lat_col]
                q_lon = row[lon_col]
                # find the shortest distance from queue point to the line point 
                dist0 = 1e12
                line_name0 = 'None'
                cap_mw0 = 0
                load_pct0 = 0
                remain_mw0 = 0
                
                # go through each transmission line
                for feature in lines_data['features']:
                    # Extract the coordinates, line capacity, load, and remaining 
                    coord_list = feature['geometry']['coordinates']
                    cap_mw = feature['properties']['Cap_MW']
                    load_pct = feature['properties']['Load_Pct']
                    remain_mw = feature['properties']['Remain_MW']
                    line_name =  feature['properties']['Name']

                    #st.write(feature['properties']['GlobalID'])
                    
                    for icoord in coord_list :
                        item = icoord[0]
                        # icoord[0] could also be list for multilinestring feature
                        if isinstance(item, list):
                            for item in icoord :
                                ilon = item[0]
                                ilat = item[1]
                                
                                dist = haversine(q_lat, q_lon, ilat, ilon)
                                if dist < dist0 :
                                    dist0 = dist
                                    cap_mw0 = cap_mw
                                    load_pct0 = load_pct
                                    remain_mw0 = remain_mw
                                    line_name0 = line_name                        
                        else :
                            ilon = icoord[0]
                            ilat = icoord[1]
                            
                            dist = haversine(q_lat, q_lon, ilat, ilon)
                            #st.write(dist)
                            if dist < dist0 :
                                dist0 = dist
                                cap_mw0 = cap_mw
                                load_pct0 = load_pct
                                remain_mw0 = remain_mw
                                line_name0 = line_name
                    
                # assigne the values from nearest line point
                queue_df.at[index,'Line_Name'] = line_name0
                queue_df.at[index,'Min_Dist'] = dist0
                queue_df.at[index,'Cap_MW'] = cap_mw0
                queue_df.at[index,'Load_Pct'] = load_pct0
                queue_df.at[index,'Remain_MW'] = remain_mw0

    
    return queue_df

#@st.cache_data
def create_altair_charts(basemap, county, county_geojson, lines_geojson, points_geojson, property_list, in_center, in_scale, coord_df) :
    # prepare for altair display 
    ca_counties = alt.Data(values=county_geojson)
    ca_lines = alt.Data(values=lines_geojson, format=alt.DataFormat(property='features', type='json'))
    
    # define map center and zoom scale 
    center = in_center
    scale = in_scale

    width = 800
    height = 600

    property_name = property_list[0]
    shape = property_list[1]
    color =  property_list[2]

    # Layering and configuring the components
    base = alt.layer(
        alt.Chart(basemap).mark_geoshape(fill='lightgray', stroke='gray').encode(tooltip=alt.value(None)),
        alt.Chart(ca_counties).mark_geoshape(fill='yellow', stroke='gray').encode(tooltip=alt.value(None)),
        alt.Chart(ca_lines).mark_geoshape(filled=False, stroke='blue').encode(tooltip=alt.Tooltip('properties.Disp_Name:N',title=''))
    ).properties(width=width, height=height)

    projections = {
        "Mercator": {
            "type": "mercator",
            "center": center,
            "rotate": [0,0,0],
            "translate": [width/2, height/2],
            "scale": scale,
            "precision": 0.1
        },
    }
    
    geo_chart = base.properties(projection=projections['Mercator'])

    alt_chart = geo_chart

    ### add extra points data ### Substations, Retired Plants, Queue Data
    #only when data is selected and there are points within county boundary
    data_tmp = None
    if points_geojson is not None and points_geojson['features']:

        #st.write(points_geojson)
        
        # convert geojson to pd df
        data_tmp = pd.json_normalize(points_geojson['features'], sep="_")
        data_tmp['longitude'] = data_tmp['geometry_coordinates'].apply(lambda x: x[0])
        data_tmp['latitude'] = data_tmp['geometry_coordinates'].apply(lambda x: x[1])

        extra_points = alt.Chart(data_tmp).mark_point(
            shape = shape,
            filled = True,
            color = color,
            size=100
        ).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=alt.Tooltip(property_name)
        )

        alt_chart = geo_chart + extra_points
    
    # add user input point
    if is_valid_coordinate(coord_df['lat'][0], coord_df['lon'][0]):
        # Create points for the input coordinates
        points = alt.Chart(coord_df).mark_point(
            shape = 'diamond',
            filled = True,
            color='#07f2ea',
            size=100
        ).encode(
            longitude='lon:Q',
            latitude='lat:Q'
        )
        
        alt_chart = alt_chart + points
    
##    multi = alt.selection_multi(on='click', nearest=False, empty = 'none', bind='legend', toggle="true")
##    geo_points = alt.Chart(subset_metrics_df).mark_circle().encode(
##        longitude='longitude:Q',
##        latitude='latitude:Q',
##        opacity=alt.condition(multi, alt.OpacityValue(1), alt.OpacityValue(0.8)),
##        size=alt.condition(multi, alt.value(selected_size),alt.value(unselected_size)),
##        shape=alt.condition(multi, alt.ShapeValue("diamond"), alt.ShapeValue("circle")),
##        tooltip='name',
##        color= alt.condition(multi, "name:N",alt.ColorValue('black'))
##    ).add_selection(
##        multi
##    )
    #return alt.vconcat(geo_chart, center=True)
    return alt_chart, data_tmp

#@st.cache_data


def main():
    # make page wide 
    st.set_page_config(page_title="Overpowered", page_icon="", layout = "wide")
    
    st.title('Overpowered - Connecting Renewable Energy to the Grid Faster')
    st.markdown("""
        <style>

            .stTabs [data-baseweb="tab-list"] {
                font-size: 20px;
                gap: 20px;
            }

            .stTabs [data-baseweb="tab"] {
                height: 50px;
                font-size: 20px;
                white-space: pre-wrap;
                background-color: #F0F2F6;
                border-radius: 10px 10px 0px 0px;
                gap: 30px;
                padding-top: 10px;
                padding-bottom: 10px;
            }

            .stTabs [aria-selected="true"] {
                background-color: #FFFFFF;
                font-size: 40px;
            }

        </style>""", unsafe_allow_html=True
    )
    
    tab1, tab2, tab3, tab4 = st.tabs(['  Home  ', '  Clustering  ', '  Power Grid Map  ', ' Details '])

##    ## Load Data
##    # US states map
##    basemap = load_basemap()
##    # CA counties map 
##    california_counties_geojson = load_geojson('data/California_County_Boundaries.geojson')

    with tab1:
        main1()

    with tab4:
        main4()

    with tab2:
        main2()

    with tab3:
        main3()
        


# home page     
def main1():
    st.write("## Introduction")

    st.write(
    """
Welcome to Overpowered! We’re a recommendation tool for power grid operators looking to streamline the Interconnection Queue approval process. 

The power grid is big and complicated, so it’s no surprise that the process of adding new power generators to the grid is too. In order to connect a generator to the grid, developers have to submit an application to the grid operator’s Interconnection Queue. The Queue is notoriously slow and often ends with developers dropping out (see “Details - The Current Queue Process” for a more in-depth explanation).

As we move towards a better, greener grid, we need an improved application process. That’s where Overpowered’s interactive tool comes in. By recommending groups of applicants to be studied together and providing visibility into the results, we can speed up processing, encourage sharing infrastructure costs, and reduce failed applications. 

Let’s get to a greener grid, faster.

    """
    )


    st.write("## Meet The Team")

    st.write(
    """
    All team members are currently pursuing their Master of Information and Data science at UC Berkeley. 
    """)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        a1, a2, a3 = st.columns([1,3,1])
        with a2:
            st.image("adam.jpg", width=200)
            st.markdown("""
            **Adam Kreitzman**  
            *(adam_kreitzman@berkeley.edu)*
            """)
        
    with c2:
        h1, h2, h3 = st.columns([1,3,1])
        with h2:
            st.image("hailee.jpg", width=200)
            st.markdown("""
            **Hailee Schuele**  
            *(hschuele@berkeley.edu)*
            """)
        
    with c3:
        
        p1, p2, p3 = st.columns([1,3,1])
        with p2:
            st.image("paul.jpg", width=200)
            st.markdown("""
            **Paul Cooper**  
            *(paul.cooper@berkeley.edu)*
            """)
    with c4:
    
        z1, z2, z3 = st.columns([1,3,1])
        with z2:
            st.image("zhifei.jpg", width=200)
            st.markdown("""
            **Zhifei Dong**   
            *(zfdong@berkeley.edu)*
            """)
    
    # st.markdown("""
    # 1. **Adam Kreitzman** *(adam_kreitzman@berkeley.edu)*
    # 2. **Hailee Schuele** *(hschuele@berkeley.edu)*
    
    # Hailee Schuele has a background in political science and public health with an environmental focus. She spent 6 years working in healthcare and pharmaceuticals as an analyst. Now she’s interested in using data science tools in support of clean energy.

    # 3. **Paul Cooper** *(paul.cooper@berkeley.edu)*
    # 4. **Zhifei Dong** *(zfdong@berkeley.edu)*

    # Zhifei Dong holds a PhD degree in coastal engineering and has 10-year experience in numerical modeling of coastal hydrodyamics (such as storm surge, waves and sediment transport), coastal resilience, restoration and adaptation, decision-support and analysis toolbox development with ArcGIS/Python programming, and LiDAR data processing. He is currently working as a geospatial data scientist.
    
    # """)

    
def main3():

    st.write("## Interactive Map")
    st.markdown("""
    Each application in the queue data indicates the county where the project is to be built. The application also briefly describes the station or transmission line it plans to connect to. Therefore, the interactive map allows the user to explore the available datasets (transmission lines, substations, retired power plants, and future infracture projects) by California counties. 

    Here are some examples of using the interactive map:
    - **Scenario 1**: The application indicates the transmission line it plans to connect to. The user can load the current queue and quickly find the shortest distance to the nearby transmission line. Additionally, the user can compare the proposed power with the remaining line capacity to determine if the transmission line has enough capacity for the application.   
    - **Scenario 2**: The application includes a power storage unit. The user can load the current queue and the retired power plants to check the availability of the nearby plants as ideal storage units.
    - **Scenario 3**: The project location of the application is far away from the existing infrastrucure. The user can load the current queue and the future infrastructure to determine if an infrastructure project is to be built near the site.   

    Currently, the querying map only supports California database. 

    """)

    st.write("### Available Datasets")
    st.markdown("""
    - **US state boundaries**: base map filled in gray color
    - **California county boundaries**: base map filled in yellow color
    - **California transmission lines**: base map lines in blue color. The transmission lines are labeled by their names and simulated remaining capacity. Hover over a transmission line to view.
    - **Additional datasets**
        - **California substations**: add-on points in "red triangle". The substations are labeled by their names. Hover over a substation to view. 
        - **Retired power plants**: add-on points in "black cross". The retired power plants are labeled by their names and dates of retirement. Hover over a plant to view.  
        - **Current queue**: add-on points in "green diamond". The queue applications are labeled by their names and station/transmission line to connect to. Hover over an application to view. 
        - **Future infrastructure**: add-on points in "purple circle". The future infrastructure projects are labeled by their names. Hover over an infrastructure project to view. 
    - **User-specified location**: add-on point in "cyan diamond". The user-specified point allows users to hand-pick a project location and explore the nearby resources.  
    """)
    
    st.write("### How to Use")
    st.markdown("""
    1. To start with, choose a California county to view. The selected county is filled with "yellow" color.

    2. Select a zoom-in scale to adjust the view as needed. 

    3. Choose an additional data layer to display. The available data layers are substations ('red triangle'), retired power plants ('black cross'), queue data ('green diamond') and future infrastructure ('purple circle').

    4. Download the table of selected data layer as needed. 

    5. This step is optional. User can enter a coordinate by latitude and longitude. The location will be displayed as "cyan diamond" on the map. 
    """)
    
    ## Load Data from Main()
    # US states map
    basemap = load_basemap()
    # CA counties map 
    california_counties_geojson = load_geojson('data/California_County_Boundaries.geojson')
    # transmission lines
    transmission_lines_geojson = load_geojson('data/TransmissionLine_CEC.geojson')
    # substations
    substations_geojson = load_geojson('data/CA_Substations_Final.geojson')
    # power plants
    plants_geojson_all = load_geojson('data/California_Power_Plants.geojson')
    # only keep retired plants
    plants_geojson = extract_retired_plants(plants_geojson_all)
    # save retired plants data to csv 
    #geojson_to_csv(plants_geojson, 'retired_plants.csv')
    
    # retired generators/ no longer use it
    #retired_gen_geojson = load_geojson('data/EIA_Retired_Generators_Y2022.geojson')

    # save shape file to geojson
    #save_shp_to_geojson('data/TransmissionLine_CES.shp')
    
    # queue data with lat/lon
    queue_df = load_csv('data/new_caiso_queue_MW.csv')
    # create a display name that combines project name and add-to substation
    queue_df['Display Name'] = queue_df['Project Name'] + " : " + queue_df["Station or Transmission Line"]

    # find the nearest transmission line and assign the capacity
    #queue_df2 =  find_nearest_line(queue_df, transmission_lines_geojson, california_counties_geojson)
    # save dataframe to csv
    #queue_df2.to_csv('data/new_caiso_queue_MW.csv', index=False)
    
    # convert dataframe to geojson for standard processing
    queue_geojson = df_to_geojson(queue_df, plants_geojson["crs"], lat_col='GIS Lat', lon_col='GIS Long')

    
    # load future infrastructure dataset
    infra_df = load_csv('data/caiso_future_transmission.csv')
    # convert dataframe to geojson for standard processing
    infra_geojson = df_to_geojson(infra_df, plants_geojson["crs"], lat_col='GIS Lat', lon_col='GIS Long')    
    
    # split display
    col1, col2 = st.columns([1, 4])
    # get a list of counties
    county_list = [feature['properties']['CountyName'] for feature in california_counties_geojson['features']]
    index_county = 0
    # create a list of scales to display
    scale_list = list(range(2500,52500,2500))
    index_scale = scale_list.index(17500)
    # create list of extra dataset to add
    #extra_data_list = ['None','Substations','Power Plants','Retired Generators']
    extra_data_list = ['None','Substations','Retired Power Plants','Current Queue','Future Infrastructure']
    index_extra = 0

    with col1:
        # create select box of counties 
        selectedCounty = st.selectbox("Choose a County to View: ", county_list, index_county)
        selectedScale = st.selectbox("Choose a Zoom-In Scale to Display: ", scale_list, index_scale)
        selectedExtra = st.selectbox("Add Additional Data to Display: ", extra_data_list, index_extra)



        # Input widgets for longitude and latitude
        st.write("**Enter a location:**")
        latitude = st.number_input("**Latitude:**", value=37.60, format="%.2f")
        longitude = st.number_input("**Longitude:**", value=-121.90, format="%.2f")
        # Create a DataFrame with the input coordinates
        coord_df = pd.DataFrame({'lat': [latitude], 'lon': [longitude]})

    with col2:
        if selectedCounty not in st.session_state.selected_county_list :
            st.session_state.selected_county_list.append(selectedCounty)
            
            # extract county data from all counties 
            county_data = extract_geojson_by_county(selectedCounty, california_counties_geojson)
            # get centroid coordinates
            centroid = get_county_centroid(county_data)
        
            # get transmission lines within the selected county
            lines_data = extract_lines_within_county(transmission_lines_geojson, county_data)

            st.session_state.selected_data_list.append([county_data, centroid, lines_data])

            #st.write(selectedCounty)
            #st.write(st.session_state.selected_data_list)
            
        else :
            index = st.session_state.selected_county_list.index(selectedCounty)
            #st.write(st.session_state.selected_county_list)
            #st.write(st.session_state.selected_data_list)

            # somehow, when runing main2(), the alameda was assigned to county list, but data list is still empty 
            try :
                county_data = st.session_state.selected_data_list[index][0]
                centroid = st.session_state.selected_data_list[index][1]
                lines_data = st.session_state.selected_data_list[index][2]
            except :
                # extract county data from all counties 
                county_data = extract_geojson_by_county(selectedCounty, california_counties_geojson)
                # get centroid coordinates
                centroid = get_county_centroid(county_data)
                # get transmission lines within the selected county
                lines_data = extract_lines_within_county(transmission_lines_geojson, county_data)
                # append items to list 
                st.session_state.selected_data_list.append([county_data, centroid, lines_data])                

        # get extra data within the selected county
        if selectedExtra == 'Substations' : 
            points_data = extract_points_within_county(substations_geojson, county_data)
            disp_shape = 'triangle'
            disp_color = 'red'
            property_name = 'properties_Name:N'
        elif selectedExtra == 'Retired Power Plants' : 
            points_data = extract_points_within_county(plants_geojson, county_data)
            disp_shape = 'cross'
            disp_color = 'black'
            property_name = 'properties_PlantName:N'
        elif selectedExtra == 'Current Queue' : 
            points_data = extract_points_within_county(queue_geojson, county_data)
            disp_shape = 'diamond'
            disp_color = 'green'
            property_name = 'properties_Display Name:N'
        elif selectedExtra == 'Future Infrastructure' : 
            points_data = extract_points_within_county(infra_geojson, county_data)
            disp_shape = 'circle'
            disp_color = '#ee07f2'
            property_name = 'properties_CAISO Transmission:N'        
        else :
            points_data = None
            property_name = 'None'
            disp_shape = 'None'
            disp_color = 'None'
        
        # altair chart
        alt_chart, data_df = create_altair_charts(basemap,selectedCounty,county_data,lines_data,points_data,[property_name,disp_shape,disp_color],
                                             centroid,selectedScale,coord_df)
        st.altair_chart(alt_chart, use_container_width=True)

        if data_df is not None:
            st.write("### Available " + selectedExtra + " data are listed below: ")
            st.write(data_df)
    
def main4() :
    st.write("## Current Queue Process")

    st.write(
        """
        There are a number of grid operators (a.k.a. ISOs/RTOs) that manage the power grid in different geographic regions of the U.S. For example, CAISO manages the grid in California. The Interconnection Queue is the process through which developers apply to add their resources to the power grid. If a developer wants to build a wind turbine, they have to get through the Queue in order to be able to sell their generated power in the grid marketplace. 

To enter the Queue, an applicant has to provide a number of materials, including a deposit, proof of land control in the area they want to build, proof of their ability to pay for the project, and the blueprints for their project design. Given the length of the Queue and manpower it takes to assess projects, grid operators take the application process seriously - they do not want to waste time on developers who are ill-prepared.

Once in the Queue, the ISO performs a series of studies to ensure the addition of the project will not disturb grid reliability and will be compatible with other projects coming online, to name a few. At the end of the study process, the ISO may return to the developer with required application updates and a price tag for the infrastructure that needs to be built to accommodate their project. Infrastructure can include line items such as additional transmission lines or energy storage. At this point, the applicant can either choose to move forward with their project (by making the updates and/or agreeing to build the infrastructure), or they can drop out. Dropout frequently results from the infrastructure costs placed on individuals. 

Moving through the Queue can take years and a large part of the bottleneck are the feasibility and system impact studies conducted by the ISO. In addition to the individual impact of a given project, the ISO has to consider how said project will interact with future infrastructure and other projects waiting in the Queue. You can imagine the added difficulty if the applicant drops out. ISOs are dealing with a complex system that’s also a moving target.

Until recently, ISOs worked through the Queue on a first in first out basis to adhere to legislation requiring each project to be given equal consideration. This worked well and good enough in the time of a few big, centralized, fossil-fuel generators. However, as the focus has shifted to renewable energy, the number of decentralized renewable generator applications has blown up. Still everyone had to wait in a single-file line and, as mentioned, the going was slow. 

Recent FERC legislation now requires ISOs to assess groups of applicants in “cluster analyses”. Depending on the ISO, there’s a short time period every year within which applicants can apply to be assessed as part of the cluster. The ISO studies the whole group, provides feedback, and then conducts a secondary study post-initial applicant dropout. 

Cluster analyses are certainly an improvement, but it’s not without its flaws. For starters, there’s a lot of pressure on developers to get their application just right within the short timeframe. If they miss the window, better luck next year. Also, while Queue times are speeding up, conducting a system-wide analysis for a large number of projects in a given cluster still takes a decent amount of time.

That’s where Overpowered comes in. By identifying smaller groups of applicants, we put more power in the hands of both ISOs and developers. ISO impact studies can be conducted more quickly if they’re able to strategically approve smaller, related groups. Small batch processing also allows for more developer flexibility since they won’t be beholden to a small application window. Finally, developers will be less likely to drop out if the cost of building new infrastructure can be shared across a group instead of born individually. Reduced dropout is good for developers who want to build, ISOs who won’t have to deal with a moving target, and the grid as a whole.

In short, our solution speeds up the Queue, provides flexibility, and reduces developer dropout. With these improvements to the Interconnection Queue, we take another step towards a green power grid.

        """
    )

    st.write("## Overpowered's Scoring Mechanism ")

    st.markdown("""
    Clusters are determined by calculating cosine similarity between a number of project features and user-specified weights. These features include:
    - Geospatial proximity
    - Line position in the Queue
    - Utility company
    - Generator type
    - Permit status
    - Current on-line date

    Projects are upweighted if they:
    - Contain energy storage
    - Are geographically close to planned infrastructure projects
    - Are geographically close to retired plants, which can be used for energy storage

    """)
    
    st.write("## Data Sources")
    
    st.markdown("""
    - CAISO’s Interconnection Queue - (ISO Generator Interconnection Queue) https://www.caiso.com/planning/Pages/GeneratorInterconnection/Default.aspx
    - CAISO’s 10 Year Transmission Plan - https://drive.google.com/file/d/1ddRU7lbQkXdpaz0cn20hKhq5JhdpWHAw/view
    - California Substation GIS - From the California Energy Commission available upon request 
    - California Transmission Line GIS - https://gis.data.ca.gov/datasets/260b4513acdb4a3a8e4d64e69fc84fee/explore
    - California Power Plants GIS - https://gis.data.ca.gov/datasets/4a702cd67be24ae7ab8173423a768e1b_0/explore
    - County Population Centroids - https://www.census.gov/geographies/reference-files/time-series/geo/centers-population.html
    - Powerflow simulation software used by ISOs

    """)
    
    st.write("## Resources")
    st.markdown("""
    If you’re interested in learning more about the problems with the Interconnection Queue, give this podcast a listen (https://www.volts.wtf/p/whats-the-deal-with-interconnection).
    

    """)
if __name__ == "__main__":
    main()
