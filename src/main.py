import streamlit as st
import pandas as pd
import requests

#Proxy for API queries



##other functions
def format_large_number(number):
    if number >= 1000000000:
        return f"{number / 1000000000:.2f} mrd NOK"
    elif number >= 1000000:
        return f"{number / 1000000:.2f} mill NOK"
    else:
        return f"{number:,}"

##visible things

uploaded_data = st.file_uploader("Input data", type=["csv"])

if uploaded_data:
    input_data = pd.read_csv(uploaded_data)
    st.write(input_data.head(5))
    column_names = list(input_data.columns)
    st.divider()

col1, col2 = st.columns(2)

with col1:
    columns = st.multiselect("Column names", column_names)
    nr_columns = len(columns)


selected_subgroups = {}
if columns:
    with col2:
        unique_occurrences = {col: input_data[col].unique().tolist() for col in columns}
        #st.write(unique_occurrences)
        for col, values in unique_occurrences.items():
            if col in input_data.select_dtypes(include=['number']).columns:
                min_value_col = input_data[col].min()                
                max_value_col = input_data[col].max()
                human_max_value_col = format_large_number(max_value_col)
                f"The {col} ranges from {min_value_col} to {human_max_value_col}"
                f"({min_value_col}-{max_value_col})"
                min_select = st.number_input("Choose min")
                max_select = st.number_input("Choose max")
                st.divider()
            else:
                selected_subgroups[col] = st.multiselect(f'Select subgroups for {col}:', values)
                st.divider()

filtered_data = input_data.copy()

for col in columns:
    if col in input_data.select_dtypes(include=['number']).columns:
        filtered_data = filtered_data[(filtered_data[col] >= min_select) & (filtered_data[col] <= max_select)]
    elif col in selected_subgroups:
        filtered_data = filtered_data[filtered_data[col].isin(selected_subgroups[col])]

st.write(filtered_data)

name_col = st.selectbox("Choose col with company names for analysis", filtered_data.columns)

for_analysis = filtered_data[name_col]

##BARD QUERY

PROMPT = f"Can you give me a csv file with all news headlines for the companies in the list: {for_analysis}"
#st.write(PROMPT)


#https://www.nbim.no/b3bb23ca-35c4-431f-930a-02607358cfae