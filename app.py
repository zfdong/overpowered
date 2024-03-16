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

@st.cache_data  # This function will be cached
def load_excel(path, sheetname):
    data = pd.read_excel(path, sheetname)
    return data

def create_altair_charts() :
    # define map center and zoom scale 
    center = [-119, 37]
    scale = 2000

    sphere = alt.sphere()
    graticule = alt.graticule(step=[5, 5])
    # lats = alt.sequence(start=-30, stop=71, step=10, as_='lats')
    # lons = alt.sequence(start=-90, stop=91, step=10, as_='lons')

    width = 800
    height = 600

    # Source of land data
    source = alt.topo_feature(data.us_10m.url, 'states')

    # CA counties map
    with open('data/California_County_Boundaries.geojson', 'r') as file:
        california_counties_geojson = json.load(file)

    ca_counties = alt.Data(values=california_counties_geojson)

    # Layering and configuring the components
    base = alt.layer(
        alt.Chart(sphere).mark_geoshape(fill='none'),
        alt.Chart(graticule).mark_geoshape(stroke='gray', strokeWidth=0.5),
        alt.Chart(source).mark_geoshape(fill='lightgray', stroke='gray'),
        alt.Chart(ca_counties).mark_geoshape(fill='lightgray', stroke='gray')
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
    Adding a new power generation facility to the grid is inefficient: takes on average 4 years and has a high rate of applicant dropout. New regulations have changed the approval process. We plan to use data techniques to create a more efficient power grid interconnection queue process by using batch processing
    """
    )

    st.write("## Intended Audience")

    st.write(
        """
        CAISO Reviewers and Developers
        """
    )
    
    st.write("## Data Sources")
    
    st.markdown(""" """)

    st.write("## Meet The Team")

    st.markdown("""
    1. **Adam Kreitzman** *(adam_kreitzman@berkeley.edu)*
    2. **Hailee Schuele** *(hschuele@berkeley.edu)*
    3. **Paul Cooper** *(paul.cooper@berkeley.edu)*
    4. **Zhifei Dong** *(zfdong@berkeley.edu)*
    """)
# cluster model 
def main2() :

    # CA counties map
    with open('data/California_County_Boundaries.geojson', 'r') as file:
        california_counties_geojson = json.load(file)
        
    county_list = [feature['properties']['CountyName'] for feature in california_counties_geojson['features']]
    
    selectedLeague = st.selectbox("Choose CA County", county_list)

    # altair chart
    st.altair_chart(create_altair_charts(), use_container_width=True)
    
    
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
    
    #return
# Interactive Map
def main3():
    st.sidebar.title("Operate Here")
    st.write("## CAISO Power Grid Map")

    # split display
    col1, col2 = st.columns([4, 1])
    options = list(leafmap.basemaps.keys())
    index = options.index("SATELLITE")

    with col2:

        basemap = st.selectbox("Select a basemap:", options, index)

    with col1:

        m = leafmap.Map(center=(36.7783, -119.4179), zoom_start=6)
        m.add_basemap(basemap)

        # add CA counties
        json_file = 'data/California_County_Boundaries.geojson'
        m.add_geojson(json_file, layer_name='CA Counties',
                      style = {"color" : "yellow",
                              "weight" : 2,
                               })        

        # add CA transmission lines
        json_file = 'data/TransmissionLine_CEC.geojson'
##        # change CRS and save 
##        gdf = gpd.read_file(json_file)
##        gdf.to_crs('EPSG:4326', inplace=True)
##        gdf.to_file(json_file, driver='GeoJSON')
        
        m.add_geojson(json_file, layer_name='CA Transmission Lines',
                      style = {"color" : "blue",
                              "weight" : 3,
                               })   

##        # add CA power plants 
##        json_file = 'data/California_Power_Plants.geojson'
##
####        with open(json_file, 'r') as f:
####            geojson_data = json.load(f)
####
####        # get coordinates from geojson
####        lats = []
####        lons = []
####        for feature in geojson_data["features"]:
####            coordinates = feature["geometry"]["coordinates"]
####            lats.append(coordinates[0])
####            lons.append(coordinates[1])
####        
####        # Create star-shaped markers
####        for lat, lon in zip(lats, lons):
####            star_icon = BeautifyIcon(icon='star',
####                                     inner_icon_style='color:red;font-size:10px;',  # Customize star color and size
####                                     background_color='transparent',
####                                     border_color='transparent')
####            folium.Marker([lat, lon], icon=star_icon).add_to(m)
##
##        style_dict ={
##                    # "stroke": True,
##                    "color": "#3388ff",
##                    "weight": 2,
##                    "opacity": 1,
##                    # "fill": True,
##                    # "fillColor": "#ffffff",
##                    "fillOpacity": 0,
##                    # "dashArray": "9"
##                    # "clickable": True,
##                }
##        m.add_geojson(json_file, style = style_dict, layer_name='CA Power Plants')
##
##        # add CA substations 
####        shp_file = 'data/CA_Substations_Final.shp'
####        # convert to geojson
####        gdf = gpd.read_file(shp_file)
####        gdf.to_crs('EPSG:4326', inplace=True)
####        json_file = shp_file.replace('.shp','.geojson')
####        gdf.to_file(json_file, driver='GeoJSON')
##        
##        json_file = 'data/CA_Substations_Final.geojson'
##        m.add_geojson(json_file, layer_name='CA Substations')
##
##        # add EIA retired generators
####        shp_file = 'data/EIA_Retired_Generators_Y2022.shp'
####        # convert to geojson
####        gdf = gpd.read_file(shp_file)
####        gdf.to_crs('EPSG:4326', inplace=True)
####        json_file = shp_file.replace('.shp','.geojson')
####        gdf.to_file(json_file, driver='GeoJSON')
##        
##        json_file = 'data/EIA_Retired_Generators_Y2022.geojson'
##        m.add_geojson(json_file, layer_name='EIA Retired Generators')        
        
        m.to_streamlit(height=700)


##    # Create a map object centered at a specific location
##    m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)
##
##    # Add the GeoJSON to the map
##    #json_file = 'TransmissionLine_CEC.geojson'
##    #json_file = 'us-states.json'
##    json_file = 'data/California_County_Boundaries.geojson'
##    folium.GeoJson(json_file, name='CAISO Transmission Line').add_to(m)
##
##    st_folium(m,width=1500, height=800)
##    
##    #folium_static(m)

if __name__ == "__main__":
    main()
