import streamlit as st
import json
import pandas as pd
# the command below causes segmentation fault on local computer
from st_aggrid import AgGrid, GridOptionsBuilder
from streamlit_extras.stylable_container import stylable_container 

@st.cache_data  # This function will be cached
def load_excel(path, sheetname):
    data = pd.read_excel(path, sheetname)
    return data
    
@st.cache_data  # This function will be cached
def load_json(path):
    return pd.read_json(path)
    

@st.cache_data # This function will be cached
def get_cluster(cluster_df, project_head):
    return pd.DataFrame.from_dict(cluster_df[cluster_df["ProjectHead"] == project_head]["Cluster"].iloc[0])


def main2():
    full_queue_df = load_excel('data/Caiso Queue Data.xlsx', 'Grid GenerationQueue')
    full_queue_df.rename(columns={full_queue_df.columns[0]: 'Project Name'}, inplace=True)
    column_ixs_to_keep = [0, 1, 2, 6, 7, 9, 15, 19, 23, 25, 27, 29, 31, 32, 33, 34, 35]
    visible_df = full_queue_df.iloc[:, column_ixs_to_keep]
    
    options_builder = GridOptionsBuilder.from_dataframe(visible_df)
    # options_builder.configure_column(‘col1’, editable=True)
    options_builder.configure_selection('single')
    options_builder.configure_pagination(paginationPageSize=10, paginationAutoPageSize=False)
    grid_options = options_builder.build()
    
    cluster_df = load_json("energy_projects_similarity.json")
        
    st.subheader("Clustering Model")
    with st.expander("Set Parameters"):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            cluster_size = st.slider(label="Cluster Size", min_value= 2, max_value = 10)
        with col2:
            w1 = st.number_input(label="Weight 1", value = 0.25)
        with col3:
            w2 = st.number_input(label="Weight 2", value = 0.25)
        with col4:
            w3 = st.number_input(label="Weight 3", value = 0.25)
        with col5:    
            w4 = st.number_input(label="Weight 4", value = 0.25)
    
    st.subheader('Select an application from the queue to suggest a cluster')

    grid_return = AgGrid(visible_df, grid_options)
    selected_rows = grid_return["selected_rows"]
    
    if 'chosen_cluster_df' not in st.session_state:
        st.session_state.chosen_cluster_df = []

    col1, col2 = st.columns([9, 1])
    
    with col1:
        go_button = st.button('Go')
    with col2:
        with stylable_container(
            key="clear_button",
            css_styles= """
                button {
                    margin-left: auto; 
                    margin-right: 0;
                }            
            """
        ):
            clear_button = st.button('Clear')
    
    if go_button:
        st.session_state.chosen_cluster_df = get_cluster(cluster_df, selected_rows[0]["Project Name"])
        
    if clear_button:
        st.session_state.chosen_cluster_df = []
    
    try:
        st.subheader(selected_rows[0]["Project Name"] + " Suggested Cluster")
        cluster_grid_return = AgGrid(st.session_state.chosen_cluster_df)
    except:
        st.write("Select a row and hit Go to continue")
        