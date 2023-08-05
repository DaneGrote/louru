"""Python file to serve as the frontend"""
import streamlit as st

import pandas as pd
import json
import datetime
import pyodbc
import snowflake.connector
from sqlalchemy import create_engine
import snowflake.sqlalchemy

from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain, create_extraction_chain_pydantic
from langchain.llms import OpenAI
from langchain.prompts import ChatPromptTemplate
from langchain import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain

OPEN_AI_API_KEY = st.secrets["open_api_key"]

SF_ACCOUNT = st.secrets["sf_account"]
SF_DATABASE = st.secrets["sf_database"]
SF_SCHEMA = st.secrets["sf_schema"]
SF_USERNAME = st.secrets["sf_username"]
SF_PASSWORD = st.secrets["sf_password"]


def sf_engine():
    conn = snowflake.connector.connect(
        user=SF_USERNAME,
        password=SF_PASSWORD,
        account=SF_ACCOUNT,
        database=SF_DATABASE,
        schema=SF_SCHEMA
    )

    connection_string = f'snowflake://{SF_USERNAME}:{SF_PASSWORD}@{SF_ACCOUNT}/{SF_DATABASE}/{SF_SCHEMA}'
    # Create an SQLAlchemy engine
    return create_engine(connection_string)


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
    input_text = st.text_area("What's poppin'? ", "")
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

tab1, tab2 = st.tabs(['Experience Management Portal', 'Experience Explorer'])

with tab1:
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
                    st.write(f"Thank you, your {form_response_df['event_type'].iloc[0]} is going to be a HIT! 🎉")
                    st.data_editor(form_response_df)
                    form_response_df.to_sql('experience_raw', con=sf_engine(), if_exists='append', index=False)

with tab2:
    
    template = """Context:  Your name is Louru, and users ask you questions about businesses in St. Louis, Missouri. Be whitty and creative in your response.

    follow these rules when answering questions: 
    1. Use the experience_raw table in the landing schema to answer the following question about businesses. 
    2. Be sure to use like keyword with wildcards when doing any text search.
    4. If doing text search in where statement, remove plurality when doing search
    5. Exscape the '$' character when replying

    Question: <prompt>
    Answer:
    """

    user_input = st.text_area("Whatcha lookin' for? ", "")

    if user_input:

        prompt = template.replace('<prompt>', user_input)

        connection_string = f'snowflake://{SF_USERNAME}:{SF_PASSWORD}@{SF_ACCOUNT}/{SF_DATABASE}/{SF_SCHEMA}'
        db = SQLDatabase.from_uri(connection_string)

        llm = OpenAI(openai_api_key=OPEN_AI_API_KEY,temperature=0)
        db_chain = SQLDatabaseChain(llm=llm, database=db, verbose=True)

        response = db_chain.run(prompt)

        if response:
            st.write(response)

