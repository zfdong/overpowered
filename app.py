import streamlit as st
from streamlit.components.v1 import html
import leafmap.foliumap as leafmap

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



@st.cache_data
def load_excel(path, sheetname):
    data = pd.read_excel(path, sheetname)
    return data

@st.cache_data
def load_county_map(file_path):
    # CA counties map
    with open(file_path, 'r') as file:
        ca_counties = json.load(file)
    return ca_counties

@st.cache_data
def load_transmission_lines(file_path):
    # transmission lines geojson
    with open(file_path, 'r') as file:
        trans_lines = json.load(file)
    return trans_lines    

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
    
def extract_lines_within_county(lines_geojson, county_geojson):
    # get county shape
    county_shape = shape(county_geojson['features'][0]['geometry'])

    within_lines = []
    for feature in lines_geojson['features'] :
        line_shape = shape(feature['geometry'])
        if line_shape.within(county_shape) :
            within_lines.append(feature)

    # create a new GeoJSON structure for within lines
    within_lines_geojson = {
        "type": "FeatureCollection",
        "crs": lines_geojson["crs"],
        "features": within_lines
    }    
    return within_lines_geojson

def create_altair_charts(county, in_geojson, lines_geojson) :
    # extract county data from all data 
    county_data = extract_geojson_by_county(county, in_geojson) 
    ca_counties = alt.Data(values=county_data)

    # get transmission lines within the selected county
    lines_data = extract_lines_within_county(lines_geojson, county_data)
    ca_lines = alt.Data(values=lines_data)
    
    # define map center and zoom scale 
    center = get_county_centroid(county_data)
    scale = 17000

    # insert centroid to the geojson
    county_data['features'][0]['properties']['centroid_lon'] = center[0]
    county_data['features'][0]['properties']['centroid_lat'] = center[1]

    sphere = alt.sphere()
    graticule = alt.graticule(step=[5, 5])

    width = 800
    height = 600

    # Source of land data
    source = alt.topo_feature(data.us_10m.url, 'states')

    # Layering and configuring the components
    base = alt.layer(
        alt.Chart(sphere).mark_geoshape(fill='none'),
        alt.Chart(graticule).mark_geoshape(stroke='gray', strokeWidth=0.5),
        alt.Chart(source).mark_geoshape(fill='lightgray', stroke='gray'),
        alt.Chart(ca_counties).mark_geoshape(fill='yellow', stroke='gray'),
##        alt.Chart(ca_counties).mark_text(align='center',baseline='middle',fontSize=10,dy=-5
##                                         ).encode(longitude='centroid_lon:Q',latitude='centroid_lat:Q',text='CountyName:N' 
##                                                  )
        alt.Chart(ca_lines).mark_geoshape(filled=False, stroke='blue')
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

    multi = alt.selection_multi(on='click', nearest=False, empty = 'none', bind='legend', toggle="true")
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
    return alt.vconcat(geo_chart, center=True)

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
# cluster model 
def main2() :
##    full_queue_df = load_excel('data/Caiso Queue Data.xlsx', 'Grid GenerationQueue')
##    full_queue_df.rename(columns={full_queue_df.columns[0]: 'Project Name'}, inplace=True)
##    column_ixs_to_keep = [0, 1, 2, 6, 7, 9, 15, 19, 23, 25, 27, 29, 31, 32, 33, 34, 35]
##    visible_df = full_queue_df.iloc[:, column_ixs_to_keep]
##    
##    options_builder = GridOptionsBuilder.from_dataframe(visible_df)
##    # options_builder.configure_column(‘col1’, editable=True)
##    options_builder.configure_selection('single')
##    options_builder.configure_pagination(paginationPageSize=10, paginationAutoPageSize=False)
##    grid_options = options_builder.build()
##
##    st.write("## Clustering Model")
##    # st.caption('Select an application from the queue to suggest a cluster')
##    grid_return = AgGrid(visible_df, grid_options)
##    selected_rows = grid_return["selected_rows"]
##    try:
##        st.header(selected_rows[0]["Project Name"] + " Suggested Cluster")
##        cluster_df = createCluster(visible_df, n=5, selectedProjectName=  selected_rows[0]["Project Name"])
##        cluster_grid_return = AgGrid(cluster_df)
##    except:
##        st.write("Select a row to continue")   
    
    return
    
def main3():
    # load and cache CA counties map 
    california_counties_geojson = load_county_map('data/California_County_Boundaries.geojson')
    # get a list of counties
    county_list = [feature['properties']['CountyName'] for feature in california_counties_geojson['features']]
    # create select box of counties 
    selectedCounty = st.selectbox("Choose a County to View", county_list)

    # load and cache transmission lines
    transmission_lines_geojson = load_transmission_lines('data/TransmissionLine_CEC.geojson')

    
    
    # altair chart
    st.altair_chart(create_altair_charts(selectedCounty, california_counties_geojson, transmission_lines_geojson), use_container_width=True)
    
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
