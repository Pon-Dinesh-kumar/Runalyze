import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import streamlit as st
import pandas as pd


def display_table_page():
    with open('failed_test_cases.json', 'r') as f:
        failed_test_cases = json.load(f)

    df = pd.DataFrame(failed_test_cases)

    with st.sidebar:
        st.header("Filters")
        num_results = st.number_input('Number of Results', min_value=1, value=10, step=1)
        search_query = st.text_input("Search by ID, Test Case ID, or Name")
        class_labels = st.multiselect("Class Label", options=df['CLASS_LABEL'].unique(), default=df['CLASS_LABEL'].unique())
        priorities = st.multiselect("Priority", options=df['PRIORITY'].unique(), default=df['PRIORITY'].unique())


    if search_query:
        df = df[df.apply(lambda row: search_query.lower() in str(row).lower(), axis=1)]
    if class_labels:
        df = df[df['CLASS_LABEL'].isin(class_labels)]
    if priorities:
        df = df[df['PRIORITY'].isin(priorities)]

    df_display = df.head(num_results)

    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=num_results)
    gb.configure_side_bar()
    gb.configure_selection('multiple', use_checkbox=True)
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()

    grid_response = AgGrid(
        df_display,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=False,
        theme='streamlit',
        height=600,
        reload_data=False
    )

st.set_page_config(layout="wide")

if __name__ == "__main__":
    display_table_page()
