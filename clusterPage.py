import streamlit as st
import json
import pandas as pd
# the command below causes segmentation fault on local computer
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
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
    if project_head  in cluster_df["ProjectHead"].values:
        new_df = pd.DataFrame.from_dict(cluster_df[cluster_df["ProjectHead"] == project_head]["Cluster"].iloc[0])
        cluster_data_df = pd.json_normalize(cluster_df[cluster_df["ProjectHead"] == "DAYLIGHT"]["Summary"].iloc[0])
        associated_projects_df = new_df.rename(columns=dict(zip(new_df.columns, [c.title() for c in new_df.columns])))
        associated_projects_df = associated_projects_df[["Project", "Project Score", "Location", "Process", "Infrastructure", "Overall"]]
    else:
        cluster_data_df = pd.DataFrame({})
        associated_projects_df = pd.DataFrame({})
    return cluster_data_df, associated_projects_df


def main2():
    # load queue data and assign column name to the first column 
    full_queue_df = load_excel('data/Caiso Queue Data.xlsx', 'Grid GenerationQueue')
    full_queue_df.rename(columns={full_queue_df.columns[0]: 'Project Name'}, inplace=True)
    # only keep selected columns 
    column_ixs_to_keep = [0, 1, 2, 6, 7, 9, 15, 19, 23, 25, 27, 29, 31, 32, 33, 34, 35]
    visible_df = full_queue_df.iloc[:, column_ixs_to_keep]
    #st.write(visible_df)
    
    options_builder = GridOptionsBuilder.from_dataframe(visible_df)
    # options_builder.configure_column(‘col1’, editable=True)
    options_builder.configure_selection('single')
    options_builder.configure_pagination(paginationPageSize=10, paginationAutoPageSize=False)
    grid_options = options_builder.build()
    
    cluster_df = load_json("corrected_projects_clusters.json")
        
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
            col1, col2 = st.columns(2)
            with col1:
                w1 = st.number_input(label="Weight 1", value = 0.25)
                w2 = st.number_input(label="Weight 2", value = 0.25)
            with col2:
                w3 = st.number_input(label="Weight 3", value = 0.25)
                w4 = st.number_input(label="Weight 4", value = 0.25)

    grid_return = AgGrid(visible_df, grid_options)
    selected_rows = grid_return["selected_rows"]

    # write out selected rows to check its format
    #st.write(selected_rows)

    col1, col2 = st.columns([9, 1])
    
    with col1:
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
        st.session_state.cluster_summary_df, st.session_state.associated_projects_df = get_cluster(cluster_df, st.session_state.selected_rows[0]["Project Name"])
        
        
    if clear_button:
        st.session_state.associated_projects_df = pd.DataFrame({})
        st.session_state.cluster_summary_df = pd.DataFrame({})
        st.session_state.selected_rows = None
    
    if st.session_state.selected_rows == None:
        st.write("Select a row and hit Go to continue")
        
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(st.session_state.selected_rows[0]["Project Name"] + " Suggested Cluster")
            if st.session_state.associated_projects_df.empty:
                st.markdown(''':red[No Cluster found]''', unsafe_allow_html=True)
            else:
                row = st.columns(len(list(st.session_state.cluster_summary_df)))
                for ix, col in enumerate(row):
                    tile = col.container(border=True)
                    
                    tile.markdown('**' + str(st.session_state.cluster_summary_df.iat[0, ix]) + '**')
                    tile.write(list(st.session_state.cluster_summary_df)[ix])

                cluster_grid_return = AgGrid(st.session_state.associated_projects_df, columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW)
        with col2:
            st.markdown('''
                :rainbow[Map Placeholder]''')
        
