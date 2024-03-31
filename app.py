import streamlit as st

# Initialize the list in st.session_state if it doesn't exist
if 'selected_county_list' not in st.session_state:
    st.session_state.selected_county_list = []
if 'selected_data_list' not in st.session_state:
    st.session_state.selected_data_list = []

from streamlit.components.v1 import html
import leafmap.foliumap as leafmap

import folium
from folium.plugins import BeautifyIcon

import json
import pandas as pd
# the command below causes segmentation fault on local computer
from st_aggrid import AgGrid, GridOptionsBuilder

import altair as alt
from vega_datasets import data

#from streamlit_folium import folium_static, st_folium

import geopandas as gpd

from shapely.geometry import shape, MultiPolygon, MultiLineString

import csv 

from clusterPage import main2

@st.cache_data
def load_basemap() :
    basemap = alt.topo_feature(data.us_10m.url, 'states')
    return basemap 

@st.cache_data
def load_excel(path, sheetname):
    data = pd.read_excel(path, sheetname)
    return data

@st.cache_data
def load_geojson(file_path):
    with open(file_path, 'r') as file:
        geojson_data = json.load(file)
    return geojson_data

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

#@st.cache_data
def create_altair_charts(basemap, county, county_geojson, lines_geojson, points_geojson, property_name, in_center, in_scale, coord_df) :
    # prepare for altair display 
    ca_counties = alt.Data(values=county_geojson)
    ca_lines = alt.Data(values=lines_geojson, format=alt.DataFormat(property='features', type='json'))
    
    # define map center and zoom scale 
    center = in_center
    scale = in_scale

    width = 800
    height = 600

    # Layering and configuring the components
    base = alt.layer(
        alt.Chart(basemap).mark_geoshape(fill='lightgray', stroke='gray'),
        alt.Chart(ca_counties).mark_geoshape(fill='yellow', stroke='gray'),
        alt.Chart(ca_lines).mark_geoshape(filled=False, stroke='blue').encode(tooltip=alt.Tooltip('properties.Name:N',title=''))
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

    # add extra points data only when data is selected and there are points within county boundary
    data_tmp = None
    if points_geojson is not None and points_geojson['features']:

        #st.write(points_geojson)
        
        # convert geojson to pd df
        data_tmp = pd.json_normalize(points_geojson['features'], sep="_")
        data_tmp['longitude'] = data_tmp['geometry_coordinates'].apply(lambda x: x[0])
        data_tmp['latitude'] = data_tmp['geometry_coordinates'].apply(lambda x: x[1])

        extra_points = alt.Chart(data_tmp).mark_point(
            filled = True,
            color='black',
            size=100
        ).encode(
            longitude='longitude:Q',
            latitude='latitude:Q',
            tooltip=property_name
        )

        alt_chart = geo_chart + extra_points
    
    # add user input point
    if is_valid_coordinate(coord_df['lat'][0], coord_df['lon'][0]):
        # Create points for the input coordinates
        points = alt.Chart(coord_df).mark_point(
            shape = 'diamond',
            filled = True,
            color='red',
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

def main():
    # make page wide 
    st.set_page_config(page_title="Overpowered", page_icon="", layout = "wide")
    
    st.title('Overpowered - Connecting Renewable Energy to the Grid Faster')
    app_choice_2 = st.selectbox('Choose Page to Navigate To:', ['Home', 'Clustering', 'Power Grid Map'])
    if app_choice_2 == 'Home':
        main1()
    elif app_choice_2 == 'Clustering':
        main2()
    elif app_choice_2 == 'Power Grid Map':
        main3()


# home page     
def main1():
    st.write("## Introduction")

    st.write(
    """
The Power Grid is big, and complicated. So it’s no surprise that adding new power generators to the grid is, too.

It is also a legacy system – built in a time of lower demand and centralized, fossil-fuel guzzling, behemoth power generators. It’s 2024, and power generators have gone green, decentralized, and multiplied, but the process for connecting generators to the grid hasn’t changed. As a result, there is a queue to join the grid more than 10,000 applications long with wait times averaging 4 years.

As we move to a better, greener grid, we need a better application process. Investigating multiple applicants at a time can speed up processing, share up-front infrastructure costs, and reduce failed applications.

Our team is building a product that will help energy regulators streamline this process by stitching together varied data sources and applying cutting edge data science techniques to identify and suggest applicants to be considered as a group.  

    """
    )

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
    
    st.write("## Data Sources")
    
    st.markdown(""" """)

    st.write("## Meet The Team")

    st.write(
    """
    All team members are currently pursuing their Master of Information and Data science at UC Berkeley. 
    """)

    st.markdown("""
    1. **Adam Kreitzman** *(adam_kreitzman@berkeley.edu)*
    2. **Hailee Schuele** *(hschuele@berkeley.edu)*
    
    Hailee Schuele has a background in political science and public health with an environmental focus. She spent 6 years working in healthcare and pharmaceuticals as an analyst. Now she’s interested in using data science tools in support of clean energy.

    3. **Paul Cooper** *(paul.cooper@berkeley.edu)*
    4. **Zhifei Dong** *(zfdong@berkeley.edu)*
    """)

    
def main3():

    st.write("## How to Use the Querying Map")

    st.markdown("""Currently, the querying map only supports CAISO database. 
    """)

    st.markdown("""
    1. To start with, choose a California county to zoom into. The county boundary is filled with "yellow" color.

    2. Select a zoom-in scale to display the transmission lines in "blue" color.

    3. Choose an extra data layer to display as "black dot". The available data layers are substations, power plants and retired generators.

    4. This is optional. User can enter a location coordinate by latitude and longitude. The location will be added to plots as "red diamond"
    """)
    
    ## Load Data
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
    geojson_to_csv(plants_geojson, 'retired_plants.csv')
    
    # retired generators
    retired_gen_geojson = load_geojson('data/EIA_Retired_Generators_Y2022.geojson')
    
    # split display
    col1, col2 = st.columns([1, 4])
    # get a list of counties
    county_list = [feature['properties']['CountyName'] for feature in california_counties_geojson['features']]
    index_county = 0
    # create a list of scales to display
    scale_list = list(range(5000,40000,2500))
    index_scale = scale_list.index(17500)
    # create list of extra dataset to add
    #extra_data_list = ['None','Substations','Power Plants','Retired Generators']
    extra_data_list = ['None','Substations','Retired Power Plants']
    index_extra = 0

    with col1:
        # create select box of counties 
        selectedCounty = st.selectbox("Choose a County to View: ", county_list, index_county)
        selectedScale = st.selectbox("Choose a Zoom-In Scale to Display: ", scale_list, index_scale)
        selectedExtra = st.selectbox("Add Additional Data to Display: ", extra_data_list, index_extra)



        # Input widgets for longitude and latitude
        st.write("**Enter a location:**")
        latitude = st.number_input("**Latitude:**", value=999.00, format="%.2f")
        longitude = st.number_input("**Longitude:**", value=999.00, format="%.2f")
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
            
        else :
            index = st.session_state.selected_county_list.index(selectedCounty)
            county_data = st.session_state.selected_data_list[index][0]
            centroid = st.session_state.selected_data_list[index][1]
            lines_data = st.session_state.selected_data_list[index][2]
            #points_data = st.session_state.selected_data_list[index][3]

        # get extra data within the selected county
        if selectedExtra == 'Substations' : 
            points_data = extract_points_within_county(substations_geojson, county_data)
            property_name = 'properties_Name:N'
        elif selectedExtra == 'Retired Power Plants' : 
            points_data = extract_points_within_county(plants_geojson, county_data)
            property_name = 'properties_PlantName:N'
##        elif selectedExtra == 'Retired Generators' : 
##            points_data = extract_points_within_county(retired_gen_geojson, county_data)
##            property_name = 'properties_Plant_Name:N'
        else :
            points_data = None
            property_name = 'None'
        
        # altair chart
        alt_chart, data_df = create_altair_charts(basemap,selectedCounty,county_data,lines_data,points_data,property_name,
                                             centroid,selectedScale,coord_df)
        st.altair_chart(alt_chart, use_container_width=True)

        if data_df is not None:
            st.write("### Available data are listed below: ")
            st.write(data_df)
    
# Interactive Map
##def main3():
##    st.sidebar.title("Operate Here")
##    st.write("## CAISO Power Grid Map")
##
##    # split display
##    col1, col2 = st.columns([4, 1])
##    options = list(leafmap.basemaps.keys())
##    index = options.index("SATELLITE")
##
##    with col2:
##
##        basemap = st.selectbox("Select a basemap:", options, index)
##
##    with col1:
##
##        m = leafmap.Map(center=(36.7783, -119.4179), zoom_start=6)
##        m.add_basemap(basemap)
##
##        # add CA counties
##        json_file = 'data/California_County_Boundaries.geojson'
##        m.add_geojson(json_file, layer_name='CA Counties',
##                      style = {"color" : "yellow",
##                              "weight" : 2,
##                               })        
##
##        # add CA transmission lines
##        json_file = 'data/TransmissionLine_CEC.geojson'
####        # change CRS and save 
####        gdf = gpd.read_file(json_file)
####        gdf.to_crs('EPSG:4326', inplace=True)
####        gdf.to_file(json_file, driver='GeoJSON')
##        
##        m.add_geojson(json_file, layer_name='CA Transmission Lines',
##                      style = {"color" : "blue",
##                              "weight" : 3,
##                               })   
##
####        # add CA power plants 
####        json_file = 'data/California_Power_Plants.geojson'
####
######        with open(json_file, 'r') as f:
######            geojson_data = json.load(f)
######
######        # get coordinates from geojson
######        lats = []
######        lons = []
######        for feature in geojson_data["features"]:
######            coordinates = feature["geometry"]["coordinates"]
######            lats.append(coordinates[0])
######            lons.append(coordinates[1])
######        
######        # Create star-shaped markers
######        for lat, lon in zip(lats, lons):
######            star_icon = BeautifyIcon(icon='star',
######                                     inner_icon_style='color:red;font-size:10px;',  # Customize star color and size
######                                     background_color='transparent',
######                                     border_color='transparent')
######            folium.Marker([lat, lon], icon=star_icon).add_to(m)
####
####        style_dict ={
####                    # "stroke": True,
####                    "color": "#3388ff",
####                    "weight": 2,
####                    "opacity": 1,
####                    # "fill": True,
####                    # "fillColor": "#ffffff",
####                    "fillOpacity": 0,
####                    # "dashArray": "9"
####                    # "clickable": True,
####                }
####        m.add_geojson(json_file, style = style_dict, layer_name='CA Power Plants')
####
####        # add CA substations 
######        shp_file = 'data/CA_Substations_Final.shp'
######        # convert to geojson
######        gdf = gpd.read_file(shp_file)
######        gdf.to_crs('EPSG:4326', inplace=True)
######        json_file = shp_file.replace('.shp','.geojson')
######        gdf.to_file(json_file, driver='GeoJSON')
####        
####        json_file = 'data/CA_Substations_Final.geojson'
####        m.add_geojson(json_file, layer_name='CA Substations')
####
####        # add EIA retired generators
######        shp_file = 'data/EIA_Retired_Generators_Y2022.shp'
######        # convert to geojson
######        gdf = gpd.read_file(shp_file)
######        gdf.to_crs('EPSG:4326', inplace=True)
######        json_file = shp_file.replace('.shp','.geojson')
######        gdf.to_file(json_file, driver='GeoJSON')
####        
####        json_file = 'data/EIA_Retired_Generators_Y2022.geojson'
####        m.add_geojson(json_file, layer_name='EIA Retired Generators')        
##        
##        m.to_streamlit(height=700)
##
##
####    # Create a map object centered at a specific location
####    m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)
####
####    # Add the GeoJSON to the map
####    #json_file = 'TransmissionLine_CEC.geojson'
####    #json_file = 'us-states.json'
####    json_file = 'data/California_County_Boundaries.geojson'
####    folium.GeoJson(json_file, name='CAISO Transmission Line').add_to(m)
####
####    st_folium(m,width=1500, height=800)
####    
####    #folium_static(m)

if __name__ == "__main__":
    main()
