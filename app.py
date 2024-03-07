import streamlit as st
from streamlit.components.v1 import html

def main():
    st.set_page_config(page_title="Overpowered", page_icon="", layout = "centered")
    st.title('Overpowered - Connecting Renewable Energy to the Grid Faster')
    app_choice_2 = st.selectbox('Choose Page to Navigate To:', ['Home', 'Clustering', 'Power Grid Map'])
    if app_choice_2 == 'HOME':
        main1()
    elif app_choice_2 == 'Clustering':
        main2()
    elif app_choice_2 == 'Power Grid Map':
        main3()
    
def main3():
    st.title('ArcGIS Online Map in Streamlit')

    # Example ArcGIS Online map URL
    map_url = "https://www.arcgis.com/apps/mapviewer/index.html?webmap=3572b0bcfb724855af36a5cb54cef1d8"

    # Define the iframe HTML code with your map URL
    iframe = f'<iframe src="{map_url}" width="100%" height="600"></iframe>'

    # Use the HTML method to display the iframe in your app
    html(iframe, height=600)

if __name__ == "__main__":
    main()
