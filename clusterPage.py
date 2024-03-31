import streamlit as st
import json
import pandas as pd
# the command below causes segmentation fault on local computer
from st_aggrid import AgGrid, GridOptionsBuilder

@st.cache_data  # This function will be cached
def load_excel(path, sheetname):
    data = pd.read_excel(path, sheetname)
    return data
    
@st.cache_data  # This function will be cached
def load_json(path):
    return pd.read_json(path)
    

@st.cache_data # This function will be cached
def get_cluster(cluster_df, project_head):
    return pd.DataFrame.from_dict(cluster_df[cluster_df["ProjectHead"] == project_head]["Cluster"][0])


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
            st.slider(label="Cluster Size", min_value= 2, max_value = 10)
        with col2:
            st.number_input(label="Weight 1", value = 0.25)
        with col3:
            st.number_input(label="Weight 2", value = 0.25)
        with col4:
            st.number_input(label="Weight 3", value = 0.25)
        with col5:    
            st.number_input(label="Weight 4", value = 0.25)
    
    st.subheader('Select an application from the queue to suggest a cluster')

    grid_return = AgGrid(visible_df, grid_options)
    selected_rows = grid_return["selected_rows"]
    try:
        st.subheader(selected_rows[0]["Project Name"] + " Suggested Cluster")
        chosen_cluster_df = get_cluster(cluster_df, selected_rows[0]["Project Name"])
        cluster_grid_return = AgGrid(chosen_cluster_df)
    except:
        st.write("Selected: " + str(cluster_df[cluster_df["ProjectHead"] == "MONTEZUMA (HIGH WINDS III)"]))
        