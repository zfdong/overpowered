import streamlit as st
from streamlit.components.v1 import html
import folium
from streamlit_folium import folium_static, st_folium
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
    st.write("## CAISO Power Grid Map")

    # Create a map object centered at a specific location
    m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

    # Add the GeoJSON to the map
    folium.GeoJson('data/TransmissionLine_CEC.geojson', name='CAISO Transmission Line').add_to(m)

    st_folium(m,width=1500, height=800)
    
    #folium_static(m)

if __name__ == "__main__":
    main()
