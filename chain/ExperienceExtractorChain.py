import streamlit as st
import pandas as pd
import json

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain

OPEN_AI_API_KEY = st.secrets["open_api_key"]

def load_experience_extraction_chain():
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

class ExperienceExtractorChain():

    def __init__(self, user_input=''):
        self.user_input = user_input

    def run(self):
        chain = load_experience_extraction_chain()
        output = chain.run(input=self.user_input)

        df = pd.DataFrame(output).iloc[0]

        #TODO: what if field not populated?
        if 'event_date' in df:
            date_df = date_convert_llm(df['event_date'])

        if 'event_start_time' in df:
            start_time_df = time_convert_llm(df['event_start_time'])

        if 'event_end_time' in df:
            end_time_df = time_convert_llm(df['event_end_time'])

        return df, date_df, start_time_df, end_time_df

    