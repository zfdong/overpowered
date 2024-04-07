import streamlit as st
import json
import pandas as pd
import st_aggrid
# the command below causes segmentation fault on local computer
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from streamlit_extras.stylable_container import stylable_container

import altair as alt
from vega_datasets import data

from shapely.geometry import shape, MultiPolygon, MultiLineString

@st.cache_data
def load_basemap() :
    basemap = alt.topo_feature(data.us_10m.url, 'states')
    return basemap 

#@st.cache_data
def load_geojson(file_path):
    with open(file_path, 'r') as file:
        geojson_data = json.load(file)
    return geojson_data

@st.cache_data
def load_csv(path):
    data = pd.read_csv(path)
    return data

#@st.cache_data  # This function will be cached
def load_excel(path, sheetname):
    data = pd.read_excel(path, sheetname)
    return data
    
@st.cache_data  # This function will be cached
def load_json(path):
    return pd.read_json(path)
    

@st.cache_data # This function will be cached
def get_cluster(cluster_df, project_head, vis_df):
    if project_head  in cluster_df["ProjectHead"].values:
        new_df = pd.DataFrame.from_dict(cluster_df[cluster_df["ProjectHead"] == project_head]["Cluster"].iloc[0])
        # add lat/lon to displayed table
        new_df = pd.merge(new_df, vis_df[['Project Name', 'GIS Lat', 'GIS Long']], left_on='Project',  right_on='Project Name', how='left')
        new_df = new_df.drop(columns=['Project Name'])
        #st.write(new_df)
        cluster_data_df = pd.json_normalize(cluster_df[cluster_df["ProjectHead"] == "DAYLIGHT"]["Summary"].iloc[0])
        associated_projects_df = new_df.rename(columns=dict(zip(new_df.columns, [c.title() for c in new_df.columns])))
        associated_projects_df = associated_projects_df[["Project", "Project Score", "Location", "Process", "Infrastructure", "Overall","Gis Lat", "Gis Long"]]
    else:
        cluster_data_df = pd.DataFrame({})
        associated_projects_df = pd.DataFrame({})
    return cluster_data_df, associated_projects_df

def set_selection_cb(selected_rows_in, cluster_df, vis_df):
    # in local python, selected_rows_in is a list, however on streamlit, it is pd df 
    if isinstance(selected_rows_in, list) :
        # for list 
        if selected_rows_in:
            with st.spinner(text="In progress..."):
                st.session_state.selected_rows = selected_rows_in
                st.session_state.cluster_summary_df, st.session_state.associated_projects_df = get_cluster(cluster_df, st.session_state.selected_rows[0]["Project Name"], vis_df)
    else :
        # for pandas dataframe 
        if not selected_rows_in.empty:
            with st.spinner(text="In progress..."):
                st.session_state.selected_rows = selected_rows_in.reset_index(drop=True)
                st.write(st.session_state.selected_rows)
                st.session_state.cluster_summary_df, st.session_state.associated_projects_df = get_cluster(cluster_df, st.session_state.selected_rows[0]["Project Name"], vis_df)
            

def reset_selection_cb():
    st.session_state.selected_rows = None
    st.session_state.cluster_summary_df = pd.DataFrame({})
    st.session_state.associated_projects_df = pd.DataFrame({})

def get_points_centroid(in_df) :
    
    return in_df['Gis Long'].mean(), in_df['Gis Lat'].mean()

def check_list_or_df_empty(in_var) :
    # check if list is empty, value is none or pandas df is empty
    # for list 
    if isinstance(in_var, list) :
        return not in_var
    # for None value 
    elif  in_var is None :
        return in_var is None 
    # for pandas data frame 
    else :
        return in_var.empty

def create_altair_charts_main2(basemap, data_tmp, in_center, in_scale) :
    # prepare for altair display 
    #ca_counties = alt.Data(values=county_geojson)

    # define map center and zoom scale 
    center = in_center
    scale = in_scale

    width = 800
    height = 600

    # Layering and configuring the components
    base = alt.layer(
        alt.Chart(basemap).mark_geoshape(fill='lightgray', stroke='gray')#.encode(tooltip='Project:N')
        #alt.Chart(ca_counties).mark_geoshape(fill='yellow', stroke='gray')
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
    
    if data_tmp is not None:
        extra_points = alt.Chart(data_tmp).mark_point(
            shape = 'diamond',
            filled = True,
            color='green',
            size=100
        ).encode(
            longitude='Gis Long:Q',
            latitude='Gis Lat:Q',
            tooltip='Project:N'
        )

        alt_chart = geo_chart + extra_points
    

    
    return alt_chart

def main2():

    ## Load Data
    # US states map
    basemap = load_basemap()
    # CA counties map 
    #california_counties_geojson = load_geojson('data/California_County_Boundaries.geojson')
    
##    # load queue data and assign column name to the first column 
##    full_queue_df = load_excel('data/Caiso Queue Data.xlsx', 'Grid GenerationQueue')
##    full_queue_df.rename(columns={full_queue_df.columns[0]: 'Project Name'}, inplace=True)
##    # only keep selected columns 
##    column_ixs_to_keep = [0, 1, 2, 6, 7, 9, 15, 19, 23, 25, 27, 29, 31, 32, 33, 34, 35]

    # need to load csv with lat/lon cooridnates 
    full_queue_df = load_csv('data/new_caiso_queue_MW.csv')
    column_ixs_to_keep = [0, 1, 2, 5, 6, 8, 14, 18, 22, 24, 26, 28, 30, 31, 32, 33, 34, 37, 38]
    visible_df = full_queue_df.iloc[:, column_ixs_to_keep]
    
    options_builder = GridOptionsBuilder.from_dataframe(visible_df)
    # options_builder.configure_column(‘col1’, editable=True)
    options_builder.configure_selection('single')
    options_builder.configure_pagination(paginationPageSize=10, paginationAutoPageSize=False)
    grid_options = options_builder.build()
    
    cluster_df = load_json("corrected_projects_clusters.json")

##    # add lat/lon to cluster_df
##    cluster_df = pd.merge(cluster_df, visible_df[['Project Name', 'GIS Lat', 'GIS Long']], left_on='ProjectHead',  right_on='Project Name', how='left')
##    cluster_df = cluster_df.drop(columns=['Project Name'])
##    st.write(cluster_df)
    
    if check_list_or_df_empty(st.session_state.selected_rows) :
         
        st.subheader("Clustering Model")
        st.markdown(
            """
            Studying one applicant at a time poses lots of challenges. With this tool, you can determine which projects make sense to study _together_.  
            We provide a structured scoring mechanism to determine the best groups, but recognize that sometimes, expert energy users would weigh parameters in different ways. Our preset weights offer a great starting point, but you can configure weights as you see fit!
            """
        )
        c1, c2 = st.columns(2)
        
        with c1:
            with st.expander("Set Parameters"):
                st.write('***Assign relative weights***')
                col1, col2 = st.columns(2)
                with col1:
                    w1 = st.number_input(label="Location", value = 0.25)
                    w2 = st.number_input(label="Process", value = 0.25)
                with col2:
                    w3 = st.number_input(label="Infrastructure", value = 0.25)
                    w4 = st.number_input(label="Project Score", value = 0.25)

        grid_return = AgGrid(visible_df, grid_options)
        selected_rows = grid_return["selected_rows"]

        # write out selected rows to check its format
        #st.write(selected_rows)

        with stylable_container(
            key="go_button",
            css_styles= """
                button {
                    background-color: green;
                    color: white;
                    border-color: green;
                }            
            """
        ):
            #st.write(type(selected_rows))
            if not isinstance(selected_rows, list) :
                # for pandas data frame type
                go_button = st.button('Go', on_click=set_selection_cb(selected_rows, cluster_df, visible_df), disabled= selected_rows.empty)
            else :
                # for list type 
                go_button = st.button('Go', on_click=set_selection_cb(selected_rows, cluster_df, visible_df), disabled= not selected_rows)
                    
    else:
        st.subheader(st.session_state.selected_rows[0]["Project Name"] + " Suggested Cluster")
        if st.session_state.associated_projects_df.empty:
            st.markdown(''':red[No Cluster found]''', unsafe_allow_html=True)
        else:
            col1, col2 = st.columns(2)
            with col1:
                
                row = st.columns(len(list(st.session_state.cluster_summary_df)))
                for ix, col in enumerate(row):
                    with col:
                        with stylable_container(
                            key = "cluster_summary_" + str(ix),
                            css_styles='''
                                {
                                    border: 2px solid;
                                    border-radius: 10px;
                                    text-align: center
                                }
                            '''
                        ):
                    
                            st.subheader(str(st.session_state.cluster_summary_df.iat[0, ix]))
                            st.write(list(st.session_state.cluster_summary_df)[ix])

                cluster_grid_return = AgGrid(st.session_state.associated_projects_df, columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)
            with col2:
                st.markdown('''
                    :rainbow[Map Placeholder]''')
                scale_list = list(range(1000,5000,500))
                index_scale = scale_list.index(2000)
                selectedScale = st.selectbox("Choose a Zoom-In Scale to Display: ", scale_list, index_scale, key='scale2')
                # get centroid coordinates
                centroid = get_points_centroid(st.session_state.associated_projects_df)
                # display cluster in the map 
                alt_chart = create_altair_charts_main2(basemap,st.session_state.associated_projects_df,centroid, selectedScale)
                st.altair_chart(alt_chart, use_container_width=True)
        
        with stylable_container(
            key="clear_button",
            css_styles= """
                button {
                    color: red;
                    border-color: red;
                }            
            """
        ):
            clear_button = st.button('Clear', on_click=reset_selection_cb)
  
