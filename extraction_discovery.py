"""Python file to serve as the frontend"""
import streamlit as st

import pandas as pd
import json
import datetime

from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain, create_extraction_chain_pydantic
from langchain.llms import OpenAI
from langchain.prompts import ChatPromptTemplate

# Sample prompts relevant to MPV
inp = """
The Hamilton Band is playing tonight at The Broadway Oyster Bar. Show starts t 7:00 PM and there is a $10 cover.
        """
inp_happy_hour = """
Wheelhouse Downtown is having a happy hour from 11-3 on 7/30. Half off domestics and $2 well drinks.
"""

OPEN_AI_API_KEY = st.secrets["open_api_key"]

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
    "required": ["business_name", "event_type"],
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
st.set_page_config(page_title="Project Louru | Alpha Extractor", page_icon=":robot:")
st.header("Experience Manager | Project Louru")
st.markdown(""" 
    Welcome to the **Louru Experience Manager** (Alpha)! To add your upcoming experience, simply provide its name, date, time, location, a brief description, and any other relevant details. 

    For example: "Post Malone is playing tonight at The Broadway Oyster Bar. Show is from 7PM to 10PM. There is a $10 cover. $2 Beers and 1/2 Well Drinks"

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
        st.write("Does the below look correct? If so press submit")
        st.write("If changes are needed, please make them before submitting.")


        with st.form('confirmationForm'):

            col1, col2 = st.columns(2)

            with col1:
                st.text_input(value=df['business_name'], label='Business Name')

                st.text_input(value=df['event_type'], label='Experience Type')
                
                if 'event_price' in df:
                    st.number_input(value=df['event_price'], label='Experience Price', min_value=0)
                
                if 'happy_hour_deal' in df:
                    st.text_input(value=df['happy_hour_deal'], label='Happy Hour Deal')

            with col2: 
                if 'band_name' in df:
                    st.text_input(value=df['band_name'], label='Band Name')

                if 'event_date' in df:
                    st.date_input(value=datetime.date(date_df['year'], date_df['month'], date_df['day']), label='Experience Date')

                if 'event_start_time' in df:
                    st.time_input(value=datetime.time(start_time_df['hour'], start_time_df['minute']), label='Experience Start Time')

                if 'event_end_time' in df:
                    st.time_input(value=datetime.time(end_time_df['hour'], end_time_df['minute']), label='Experience End Time')


            submit = st.form_submit_button('Submit')

            if submit:
                'Thank you!'


