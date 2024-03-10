import streamlit as st
from streamlit.components.v1 import html
import leafmap.foliumap as leafmap

import folium
from folium.plugins import BeautifyIcon

import json


#from streamlit_folium import folium_static, st_folium

import geopandas as gpd

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
    st.write("## Clustering Model")

    st.write(
    """
    Link the model here.
    """
    )
    
##def main3():
##    st.title('ArcGIS Online Map in Streamlit')
##
##    # Example ArcGIS Online map URL
##    map_url = "https://www.arcgis.com/apps/mapviewer/index.html?webmap=3572b0bcfb724855af36a5cb54cef1d8"
##
##    # Define the iframe HTML code with your map URL
##    iframe = f'<iframe src="{map_url}" width="100%" height="600"></iframe>'
##
##    # Use the HTML method to display the iframe in your app
##    html(iframe, height=600)

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

        # add CA power plants 
        json_file = 'data/California_Power_Plants.geojson'

##        with open(json_file, 'r') as f:
##            geojson_data = json.load(f)
##
##        # get coordinates from geojson
##        lats = []
##        lons = []
##        for feature in geojson_data["features"]:
##            coordinates = feature["geometry"]["coordinates"]
##            lats.append(coordinates[0])
##            lons.append(coordinates[1])
##        
##        # Create star-shaped markers
##        for lat, lon in zip(lats, lons):
##            star_icon = BeautifyIcon(icon='star',
##                                     inner_icon_style='color:red;font-size:10px;',  # Customize star color and size
##                                     background_color='transparent',
##                                     border_color='transparent')
##            folium.Marker([lat, lon], icon=star_icon).add_to(m)

        style_dict ={
                    # "stroke": True,
                    "color": "#3388ff",
                    "weight": 2,
                    "opacity": 1,
                    # "fill": True,
                    # "fillColor": "#ffffff",
                    "fillOpacity": 0,
                    # "dashArray": "9"
                    # "clickable": True,
                }
        m.add_geojson(json_file, style = style_dict, layer_name='CA Power Plants')

        # add CA substations 
##        shp_file = 'data/CA_Substations_Final.shp'
##        # convert to geojson
##        gdf = gpd.read_file(shp_file)
##        gdf.to_crs('EPSG:4326', inplace=True)
##        json_file = shp_file.replace('.shp','.geojson')
##        gdf.to_file(json_file, driver='GeoJSON')
        
        json_file = 'data/CA_Substations_Final.geojson'
        m.add_geojson(json_file, layer_name='CA Substations')

        # add EIA retired generators
##        shp_file = 'data/EIA_Retired_Generators_Y2022.shp'
##        # convert to geojson
##        gdf = gpd.read_file(shp_file)
##        gdf.to_crs('EPSG:4326', inplace=True)
##        json_file = shp_file.replace('.shp','.geojson')
##        gdf.to_file(json_file, driver='GeoJSON')
        
        json_file = 'data/EIA_Retired_Generators_Y2022.geojson'
        m.add_geojson(json_file, layer_name='EIA Retired Generators')        
        
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
