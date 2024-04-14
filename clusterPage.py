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
    
def safe_round(val, precision = 4):
    try:
        return round(val, precision)
    except:
        return val
      
@st.cache_data # This function will be cached
def get_cluster(cluster_df, project_head, vis_df, weight_list, threshold = 0.6):
    if project_head  in cluster_df["ProjectHead"].values:
        new_df = pd.DataFrame.from_dict(cluster_df[cluster_df["ProjectHead"] == project_head]["Cluster"].iloc[0])
        # add lat/lon to displayed table
        new_df = pd.merge(new_df, vis_df[['Project Name', 'GIS Lat', 'GIS Long', 'Type-1', 'Net MWs to Grid', 'Remain_MW']], left_on='Project',  right_on='Project Name', how='left')
        new_df = new_df.drop(columns=['Project Name'])
        #st.write(new_df)
        # only select the first three columns in the summary, ignore the geolocations 
        cluster_data_df = pd.json_normalize(cluster_df[cluster_df["ProjectHead"] == project_head]["Summary"].iloc[0]).iloc[:,[0,1,2]]
        cluster_data_df.fillna(value=0, inplace=True)
        
        associated_projects_df = new_df[["Project",'Net MWs to Grid', "Likelihood of Approval", "Location", "Process", "Infrastructure", "Overall","GIS Lat", "GIS Long", 'Type-1', 'Remain_MW']]
        associated_projects_df.fillna(value=associated_projects_df['Likelihood of Approval'].mean(), inplace=True)
        # Scale values
        scaled_weights = [x/sum(weight_list) for x in weight_list]
        associated_projects_df['Overall'] = associated_projects_df[["Likelihood of Approval", "Location", "Process", "Infrastructure"]].mul(scaled_weights, axis=1).sum(axis=1)
        
        # Filter above threshold
        associated_projects_df = associated_projects_df[associated_projects_df['Overall'] > threshold].sort_values(by=['Overall', 'Likelihood of Approval'], ascending=False)
        
        cluster_data_df["Cluster Strength"] = associated_projects_df['Overall'].mean()
        cluster_data_df["Likelihood of Approval"] = associated_projects_df['Likelihood of Approval'].mean()
        cluster_data_df['Net Transmission Capacity'] = associated_projects_df['Net MWs to Grid'].sum() - associated_projects_df['Remain_MW'].sum()
        
        # round Likelyhood of Approval, location, process, overall
        associated_projects_df['Likelihood of Approval'] = associated_projects_df['Likelihood of Approval'].round(4)
        associated_projects_df['Location'] = associated_projects_df['Location'].round(4)
        associated_projects_df['Process'] = associated_projects_df['Process'].round(4)
        associated_projects_df['Overall'] = associated_projects_df['Overall'].round(4)
        # round the cluster strength, net transmission capacity, likelyhood of approval
        cluster_data_df['Cluster Strength'] = safe_round(cluster_data_df['Cluster Strength'])
        cluster_data_df['Net Transmission Capacity'] = safe_round(cluster_data_df['Net Transmission Capacity'], 1)
        cluster_data_df['Likelihood of Approval'] = safe_round(cluster_data_df['Likelihood of Approval'])
        
    else:
        cluster_data_df = pd.DataFrame({})
        associated_projects_df = pd.DataFrame({})
    return cluster_data_df, associated_projects_df

def set_selection_cb(selected_rows_in, cluster_df, vis_df, weight_list = [0.25,0.25,0.25,0.25]):
    # in local python, selected_rows_in is a list, however on streamlit, it is pd df 
    if isinstance(selected_rows_in, list) :
        # for list 
        if selected_rows_in:
            st.session_state.selected_rows = selected_rows_in
            st.session_state.cluster_summary_df, st.session_state.associated_projects_df = get_cluster(cluster_df, st.session_state.selected_rows[0]["Project Name"], vis_df, weight_list)
    elif isinstance(selected_rows_in, pd.DataFrame) :
        # for pandas dataframe 
        if not selected_rows_in.empty:
            st.session_state.selected_rows = selected_rows_in
            st.session_state.cluster_summary_df, st.session_state.associated_projects_df = get_cluster(cluster_df, st.session_state.selected_rows["Project Name"].iloc[0], vis_df, weight_list)
    else:
        st.session_state.selected_rows = None
        st.session_state.cluster_summary_df = pd.DataFrame({})
        st.session_state.associated_projects_df = pd.DataFrame({})

def reset_selection_cb():
    st.session_state.selected_rows = None
    st.session_state.cluster_summary_df = pd.DataFrame({})
    st.session_state.associated_projects_df = pd.DataFrame({})

def get_points_centroid(in_df) :
    
    return in_df['GIS Long'].mean(), in_df['GIS Lat'].mean()

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

def create_altair_charts_main2(basemap, data_tmp, in_center, in_scale, project_head) :
    # prepare for altair display 
    #ca_counties = alt.Data(values=county_geojson)

    # define map center and zoom scale 
    center = in_center
    scale = in_scale

    width = 300
    height = 600

    # Layering and configuring the components
    base = alt.layer(
        alt.Chart(basemap).mark_geoshape(fill='lightgray', stroke='gray').encode(tooltip=alt.value(None))
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
    # combine project head with cluster
    map_points_df = data_tmp
    map_points_df['is_project_head'] = 0
    project_head = project_head.rename(columns=dict(zip(project_head.columns, [c.title() for c in project_head.columns])))
    project_head['is_project_head'] = 1
    project_head.rename(columns={"Project Name": "Project", "Gis Long": "GIS Long", "Gis Lat": "GIS Lat"}, inplace=True)
    map_points_df = pd.concat([map_points_df[['Project', 'GIS Long', 'GIS Lat', 'Type-1', 'is_project_head']], project_head[['Project', 'GIS Long', 'GIS Lat', 'Type-1', 'is_project_head']]])
    
    
    if map_points_df is not None:
        extra_points = alt.Chart(map_points_df).mark_point(
            filled = True,
            opacity = 0.5
        ).encode(
            longitude='GIS Long:Q',
            latitude='GIS Lat:Q',
            tooltip='Project:N',
            size = alt.Size('is_project_head:N', scale=alt.Scale(domain=[0, 1], range=[100, 400])),
            shape = alt.Shape('is_project_head:N', legend=None, scale=alt.Scale(domain=[0, 1], range=['circle', 'cross'])),
            color= alt.Color('Type-1:N', scale = alt.Scale(domain=['Photovoltaic', 'Wind Turbine', 'Storage', 'Steam Turbine', 'Hydro', 'Gas Turbine', 'Solar Thermal', 'Combined Cycle'], range=['gold', '#0FD00B', '#252523', 'red', 'blue', '#D52EEE', '#0884C6', 'green']))
        )

        alt_chart = geo_chart + extra_points
    
    return alt_chart

def main2():

    ## Load Data
    # US states map
    basemap = load_basemap()
    # CA counties map 
    #california_counties_geojson = load_geojson('data/California_County_Boundaries.geojson')
    
    # need to load csv with lat/lon cooridnates 
    full_queue_df = load_csv('data/new_caiso_queue_MW.csv')
    column_ixs_to_keep = [0, 1, 2, 5, 6, 8, 14, 18, 22, 24, 26, 28, 30, 31, 32, 33, 34, 37, 38, 50]
    visible_df = full_queue_df.iloc[:, column_ixs_to_keep]
    
    options_builder = GridOptionsBuilder.from_dataframe(visible_df)
    options_builder.configure_selection('single')
    options_builder.configure_pagination(paginationPageSize=10, paginationAutoPageSize=False)
    grid_options = options_builder.build()
    
    cluster_df = load_json("final_clusters_still_nan.json")  
    
    # st.write(alt.__version__)
    if check_list_or_df_empty(st.session_state.selected_rows) :
        st.subheader("Let’s get to clustering!")

        st.markdown(
            """
            Studying a single application at a time makes for a slow going. Overpowered’s clustering tool helps you determine which projects make sense to study together. This tool focuses on the California grid operator (CAISO) Interconnection Queue.

            """
        )         
        st.subheader("Set Custom Weights")
        st.markdown(
            """
            Overpowered provides a structured scoring mechanism to determine the best groups of applicants to study together. Our default weights were determined using machine learning on historical CAISO data. These algorithms gave us insight into which features are most important for successful Queue applications.
            That said, we recognize that expert energy users may opt to weigh parameters in different ways. Our preset weights offer a great starting point, but feel free to configure them as you see fit!
             """
        )
        c1, c2 = st.columns(2)
        
        with c1:
            with st.expander("Set Parameters"):
                st.write('***Assign relative weights***')
                col1, col2 = st.columns(2)
                with col1:
                    w1 = st.number_input(label="Location", value = st.session_state.w1)
                    w2 = st.number_input(label="Process", value = st.session_state.w2)
                with col2:
                    w3 = st.number_input(label="Infrastructure", value = st.session_state.w3)
                    w4 = st.number_input(label="Likelihood of Approval", value = st.session_state.w4)

        st.subheader("Pick a Project")
        st.markdown(
            """
            Now that you’ve set your weights, click a base project in the CAISO Queue below to generate cluster recommendations.
             """
        )

        grid_return = AgGrid(visible_df, grid_options)
        selected_rows = grid_return["selected_rows"]

        # write out selected rows to check its format
        #st.write(type(selected_rows[0]))

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
            if isinstance(selected_rows, list):
                # for list type 
                go_button = st.button('Go', on_click=set_selection_cb(selected_rows, cluster_df, visible_df, [st.session_state.w4, st.session_state.w1, st.session_state.w2, st.session_state.w3]), disabled= not selected_rows)
                if go_button:
                    st.session_state.w1 = w1
                    st.session_state.w2 = w2
                    st.session_state.w3 = w3
                    st.session_state.w4 = w4
            
            elif isinstance(selected_rows, pd.DataFrame):
                # for pandas data frame type
                go_button = st.button('Go', on_click=set_selection_cb(selected_rows, cluster_df, visible_df, [st.session_state.w4, st.session_state.w1, st.session_state.w2, st.session_state.w3]), disabled= selected_rows.empty)
                if go_button:
                    st.session_state.w1 = w1
                    st.session_state.w2 = w2
                    st.session_state.w3 = w3
                    st.session_state.w4 = w4
            else:
                go_button = st.button('Go', disabled= True)
                
                    
    else:
        
        # when it is a list of dict 
        if isinstance(st.session_state.selected_rows,list) :
            st.subheader(st.session_state.selected_rows[0]["Project Name"] + " Suggested Cluster")
        # when it is a pandas data frame 
        else :
            st.subheader(st.session_state.selected_rows["Project Name"].iloc[0] + " Suggested Cluster")
            
        if st.session_state.associated_projects_df.empty:
            st.markdown(''':red[No Cluster found]''', unsafe_allow_html=True)
        else:
            
                
            col1, col2 = st.columns([3, 2])
        
            with col1:
                with st.expander("Set Parameters"):
                    st.write('***Assign relative weights***')
                    c1, c2 = st.columns(2)
                    with c1:
                        w1 = st.number_input(label="Location", value = st.session_state.w1)
                        w2 = st.number_input(label="Process", value = st.session_state.w2)
                        
                    with c2:
                        w3 = st.number_input(label="Infrastructure", value = st.session_state.w3)
                        w4 = st.number_input(label="Likelihood of Approval", value = st.session_state.w4)
                    with stylable_container(
                        key="rerun_button_ct",
                        css_styles= """
                            button {
                                background-color: green;
                                color: white;
                                border-color: green;
                            }            
                        """
                    ):
                        
                        st.button(label= "Rerun", key="rerun_btn")
                        if st.session_state.get("rerun_btn"):
                            st.session_state.w1 = w1
                            st.session_state.w2 = w2
                            st.session_state.w3 = w3
                            st.session_state.w4 = w4
                            set_selection_cb(st.session_state.selected_rows, cluster_df, visible_df, [st.session_state.w4, st.session_state.w1, st.session_state.w2, st.session_state.w3])
                        
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

                cluster_grid_return = AgGrid(st.session_state.associated_projects_df.iloc[:,0:7], columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)
            with col2:
                #st.markdown('''
                #    :rainbow[Map Placeholder]''')
                scale_list = list(range(1000,25000,1000))
                index_scale = scale_list.index(2000)
                selectedScale = st.selectbox("Choose a Zoom-In Scale to Display: ", scale_list, index_scale, key='scale2')
                # get centroid coordinates
                centroid = get_points_centroid(st.session_state.associated_projects_df)
                # display cluster in the map 
                if isinstance(st.session_state.selected_rows,list) :
                    alt_chart = create_altair_charts_main2(basemap,st.session_state.associated_projects_df,centroid, selectedScale, pd.DataFrame(st.session_state.selected_rows))
                else:
                    alt_chart = create_altair_charts_main2(basemap,st.session_state.associated_projects_df,centroid, selectedScale, st.session_state.selected_rows)
                
                with st.container(border=True):
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
        st.subheader("Variable Definitions")    
        st.markdown(
            """
            Here we can see the high-level details of the cluster recommendation.
        - **Cluster Score**: This tells you the strength of the cluster as a whole. It’s the average similarity score between the base project you selected above and all the other projects in the recommended cluster.
        - **Total MegaWatts**: This metric gives us insight into the amount of infrastructure (transmission lines and/or storage) that would need to be built to accommodate this cluster.
            - (Sum of MWs supplied to the grid for all projects in the cluster) - (Sum of available transmission capacity at each project’s proposed interconnect point)
        - **Likelihood of Approval**: The likelihood of approval is calculated for each project using features learned from historical data. This likelihood score takes the average approval of all projects in the recommended cluster.

        The table above allows us to dig into the details of each project in the cluster. Similarity scores are calculated for different categories between the base project and all other projects. The most similar projects are included in the cluster. A higher number indicates a better similarity score. (See “Details - Overpowered’s Scoring Mechanism” for more information.)
        - **Likelihood of Approval**: This is the likelihood that a given project would succeed independent of the rest of the cluster, based on past project applications.
        - **Location**: This measures the geospatial proximity between two projects.
        - **Process**: This summarizes the readiness of each project. It includes operational variables, such as the project’s position in the Queue, the date it's expected to go online, and its permit status. We want to discourage “line skipping” by grouping projects that are closer together in the Queue. We also want to encourage ease of construction and real-life operations by having projects in the same geography go online at similar times.
        - **Infrastructure**: This captures the similarity of the project build types. For example, two solar projects can be studied under the same set of assumptions, which is more efficient than two projects of different types.
        - **Overall**: The overall similarity score between the base project and the given project.
            """
        )
  
