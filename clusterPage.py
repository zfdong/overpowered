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
    new_df = pd.DataFrame.from_dict(cluster_df[cluster_df["ProjectHead"] == project_head]["Cluster"].iloc[0])
    return new_df.rename(columns=dict(zip(new_df.columns, [c.title() for c in new_df.columns])))


def main2():
    # load queue data and assign column name to the first column 
    full_queue_df = load_excel('data/Caiso Queue Data.xlsx', 'Grid GenerationQueue')
    full_queue_df.rename(columns={full_queue_df.columns[0]: 'Project Name'}, inplace=True)
    # only keep selected columns 
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

    #AgGrid(visible_df, grid_options)
    selected_rows = AgGrid(visible_df, grid_options)["selected_rows"]

    # write out selected rows to check its format
    #st.write(selected_rows)
    
    # define initial lists in app.py
##    if 'selected_rows' not in st.session_state:
##        st.session_state.selected_rows = None
##    
##    if 'chosen_cluster_df' not in st.session_state:
##        st.session_state.chosen_cluster_df = []

    col1, col2 = st.columns([9, 1])
    
    with col1:
        go_button = st.button('Go')
    with col2:
        with stylable_container(
            key="clear_button",
            css_styles= """
                button {
                    color: red;
                    float: right;
                    border-color: red;
                }            
            """
        ):
            clear_button = st.button('Clear')
    
    if go_button:
        st.session_state.selected_rows = selected_rows
        st.session_state.chosen_cluster_df = get_cluster(cluster_df, st.session_state.selected_rows[0]["Project Name"])
        
    if clear_button:
        st.session_state.chosen_cluster_df = []
        st.session_state.selected_rows = None
    
    if st.session_state.selected_rows == None:
        st.write("Select a row and hit Go to continue")
        
    else:
        st.subheader(st.session_state.selected_rows[0]["Project Name"] + " Suggested Cluster")
        cluster_grid_return = AgGrid(st.session_state.chosen_cluster_df)
        
