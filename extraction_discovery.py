"""Python file to serve as the frontend"""
import streamlit as st

import pandas as pd
import json
import datetime
from sqlalchemy import create_engine

from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain, create_extraction_chain_pydantic
from langchain.llms import OpenAI
from langchain.prompts import ChatPromptTemplate

OPEN_AI_API_KEY = st.secrets["open_api_key"]

SQL_SERVER_NAME = st.secrets["sql_server_name"]
SQL_DATABASE = st.secrets["sql_database"]
SQL_USERNAME = st.secrets["sql_username"]
SQL_PASSWORD = st.secrets["sql_password"]
SQL_DRIVER = st.secrets["sql_driver"]


# Establish a connection
params = f"Driver={SQL_DRIVER};Server=tcp:{SQL_SERVER_NAME}.database.windows.net,1433;Database={SQL_DATABASE};Uid={SQL_USERNAME};Pwd={SQL_PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)

# Defines what model should be attempting to extract from user prompt
schema = {
    "properties": {
        "business_name": {"type": "string"},
        "event_type": {"type": "string"},
        "event_price": {"type": "integer"},
        "event_date": {"type": "string"},
        "event_start_time": {"type": "string"},
        "event_end_time": {"type": "string"},
        "band_name": {"type": "string"},
        "happy_hour_deal": {"type": "string"},
    },
    "required": ["business_name", "event_type", "event_date"],
}

def get_text():
    input_text = st.text_area("What's poppin'? ", "", key="input")
    return input_text

def load_experience_extraction_chain():
    llm = ChatOpenAI(openai_api_key=OPEN_AI_API_KEY, temperature=0, model="gpt-3.5-turbo-0613")
    chain = create_extraction_chain(schema, llm)
    return chain

def date_convert_llm(event_date):
    # Convert dates and times from user input into correct syntax
    datetime_convert_llm = OpenAI(openai_api_key=OPEN_AI_API_KEY, temperature=0)
    date_prompt= """
        Convert the below date into the format of the below json object schema. Only respond with the output. 
        Today's date is 8/4/2023

        schema: {"year": {"type": "integer"}, "month": {"type": "integer"}, "day": {"type": "integer"}}
        Date: <date>
    """
    date_prompt = date_prompt.replace('<date>', event_date)
    date_response = json.loads(datetime_convert_llm(date_prompt))
    return pd.DataFrame(date_response, index=[0]).iloc[0]


def time_convert_llm(event_time):
    # Convert times from user input into correct syntax
    datetime_convert_llm = OpenAI(openai_api_key=OPEN_AI_API_KEY, temperature=0)
    time_prompt= """
        Convert the below times into the format of the below schema defining a json object. 
        Only respond with the output. 

        schema: {"hour": {"type": "integer"}, "minute": {"type": "integer"}}
        Time: <time>
    """
    time_prompt = time_prompt.replace('<time>', event_time)
    time_response = json.loads(datetime_convert_llm(time_prompt))
    return pd.DataFrame(time_response, index=[0]).iloc[0]


# UI
st.set_page_config(page_title="Project Louru | Experience Portal", page_icon=":robot:")
st.header("Louru Experience Portal (Alpha)🎸🍝🍻")
st.markdown(""" 
    Welcome to the **Louru Experience Portal** (Alpha)! To add your upcoming experience, simply provide its name, date, time, location, a brief description, and any other relevant details. 

    For example: "Post Malone is playing tonight at The Broadway Oyster Bar. Show is from 7PM to 10PM. There is a $10 cover.  Deals are 1/2 Well Drinks and apps"

    Let's share your event with the community and make it a memorable experience for everyone!
""")
st.write('')
st.write('')

user_input = get_text()

if user_input:
    chain = load_experience_extraction_chain()
    output = chain.run(input=user_input)

    df = pd.DataFrame(output).iloc[0]

    #st.data_editor(df)

    #TODO: what if field not populated?
    if 'event_date' in df:
        date_df = date_convert_llm(df['event_date'])

    if 'event_start_time' in df:
        start_time_df = time_convert_llm(df['event_start_time'])

    if 'event_end_time' in df:
        end_time_df = time_convert_llm(df['event_end_time'])
    

    with st.chat_message("user"):
        st.write("Thanks 🙏 Please confirm we understood you correctly, and press submit to share your awesome experience with the world!")
        st.write("Feel free to make changes to the below before submitting.")


        with st.form('confirmationForm'):

            form_data_structure = {
                'business_name': pd.Series(dtype='object'),      
                'event_type': pd.Series(dtype='object'),    
                'event_price': pd.Series(dtype='int'),    
                'event_date': pd.Series(dtype='datetime64[ns]'),    
                'event_start_time': pd.Series(dtype='datetime64[ns]'),    
                'event_end_time': pd.Series(dtype='datetime64[ns]'),    
                'band_name': pd.Series(dtype='object'),
                'happy_hour_deal': pd.Series(dtype='object')   
            }
            form_response_df = pd.DataFrame(form_data_structure)
            form_response_df.loc[df.shape[0]] = [None] * form_response_df.shape[1]

            col1, col2 = st.columns(2)

            with col1:
                if 'business_name' in df:
                    form_response_df['business_name'].iloc[0]= st.text_input(value=df['business_name'], label='Business Name')

                if 'event_type' in df:
                    form_response_df['event_type'] = st.text_input(value=df['event_type'], label='Experience Type')
                
                if 'event_price' in df:
                    form_response_df['event_price'] = st.number_input(value=df['event_price'], label='Experience Price', min_value=0)
                
                if 'happy_hour_deal' in df:
                    form_response_df['happy_hour_deal'] = st.text_input(value=df['happy_hour_deal'], label='Happy Hour Deal')

            with col2: 
                if 'band_name' in df:
                    form_response_df['band_name'] = st.text_input(value=df['band_name'], label='Band Name')

                if 'event_date' in df:
                    form_response_df['event_date'] = st.date_input(value=datetime.date(date_df['year'], date_df['month'], date_df['day']), label='Experience Date')

                if 'event_start_time' in df:
                    form_response_df['event_start_time'] = st.time_input(value=datetime.time(start_time_df['hour'], start_time_df['minute']), label='Experience Start Time')

                if 'event_end_time' in df:
                    form_response_df['event_end_time'] = st.time_input(value=datetime.time(end_time_df['hour'], end_time_df['minute']), label='Experience End Time')


            submit = st.form_submit_button('Submit')

            if submit:
                'Thank you!'
                st.data_editor(form_response_df)
                form_response_df.to_sql('extraction_tst', con=engine, if_exists='append', index=False, schema='louru')


