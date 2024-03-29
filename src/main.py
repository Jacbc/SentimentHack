import streamlit as st
import pandas as pd
import requests
import openai
import time
import altair as alt
import re

#OPENAI for API queries, need key
openai.api_key = ""


##other functions
def format_large_number(number):
    if number >= 1000000000:
        return f"{number / 1000000000:.2f} mrd NOK"
    elif number >= 1000000:
        return f"{number / 1000000:.2f} mill NOK"
    else:
        return f"{number:,}"


uploaded_data = st.file_uploader("Input data", type=["csv"])

if uploaded_data:
    input_data = pd.read_csv(uploaded_data)
    st.write(input_data.head(5))
    column_names = list(input_data.columns)
    st.divider()

col1, col2 = st.columns(2)

with col1:
    columns = st.multiselect("Select columns", column_names)
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

for_analysis = filtered_data['name'].to_list()

col3, col4 = st.columns(2)
with col3:
    start_date = st.date_input("Choose a start date")

with col4:
    end_date = st.date_input("Choose an end date")

##QUERY to BARD
PROMPT = f"Can you give me a csv file with all news headlines for the companies in the list: {for_analysis}, starting from {start_date} until {end_date}"
##

submit = st.button("Get headlines and their sentiment", type="primary")

sentiments = []

if submit:
    headlines = pd.read_csv("./src/SMK_Corp.csv")
    #st.write(headlines)
    for row in headlines['Headline']:
        if row.startswith(for_analysis[0]):
            row = row[len(for_analysis[0]):].strip()
        query = f"Analyse the sentiment of this text: {row}"
        #st.write(query)
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=query,
            temperature=0,
            max_tokens=128,
            n=1,
            stop=None,
            timeout=10,)
        sentiment = response.choices[0].text.strip().replace("The sentiment of the text is ", "").rstrip('.')
            # Map the sentiment to a numeric score
        if "positive" in sentiment:
            sentiment_score = 1
        elif "negative" in sentiment:
            sentiment_score = -1
        elif "neutral" in sentiment:
            sentiment_score = 0
        sentiments.append(sentiment_score)
        time.sleep(0.5)
    headlines['Sentiment'] = sentiments

headlines.to_csv("headlines_sentiment.csv", index=False)


sentiment_data = pd.read_csv("headlines_sentiment.csv")
stock_data = pd.read_csv("./src/SMK_stockprice.csv")


stock_data['Date'] = pd.to_datetime(stock_data['time'])
sentiment_data['Date'] = pd.to_datetime(sentiment_data['Date'])

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

stock_data = stock_data[(stock_data['Date'] >= start_date) & (stock_data['Date'] <= end_date)]

st.divider()

# Display the sentiment chart
sentiment_chart = alt.Chart(sentiment_data).mark_bar().encode(
    x='Date:T',
    y=alt.Y('Sentiment:Q', stack='zero'),
    color=alt.Color('Sentiment:Q', scale=alt.Scale(domain=[-1, 1], range=['red', 'green']), legend=None),
    tooltip=['Date:T', 'Sentiment:Q']
).properties(width=400, height=300)


# Display the price chart
price_chart = alt.Chart(stock_data).mark_line().encode(
    x='Date:T',
    y=alt.Y('price:Q', scale=alt.Scale(domain=[stock_data['price'].min(), stock_data['price'].max()])),
    tooltip=['date:T', 'price:Q']
).properties(width=400, height=300)



st.subheader('Sentiment Chart')
st.altair_chart(sentiment_chart, use_container_width=True)
st.subheader('Price Chart')
st.altair_chart(price_chart, use_container_width=True)


