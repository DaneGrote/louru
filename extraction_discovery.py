"""Python file to serve as the frontend"""
import streamlit as st

import pandas as pd
import json

from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain, create_extraction_chain_pydantic
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
        "happy_hour_start_time": {"type": "string"},
        "happy_hour_end_time": {"type": "string"},
        "happy_hour_deal": {"type": "string"},
    },
    "required": ["business_name", "event_type"],
}

def load_chain():
    llm = ChatOpenAI(openai_api_key=OPEN_AI_API_KEY, temperature=0, model="gpt-3.5-turbo-0613")
    chain = create_extraction_chain(schema, llm)
    return chain

chain = load_chain()

st.set_page_config(page_title="Project Louru | Alpha Extractor", page_icon=":robot:")
st.header("Project Louru | Alpha Extractor")
st.markdown(""" 
    Welcome to the **Louru Experience Manager** (Alpha)! To add your upcoming experience, simply provide its name, date, time, location, a brief description, and any other relevant details. 

    For example: "Post Malone is playing tonight at The Broadway Oyster Bar. Show starts at 7:00 PM, and there is a $10 cover.

    Let's share your event with the community and make it a memorable experience for everyone!
""")


def get_text():
    input_text = st.text_input("What's poppin'? ", "", key="input")
    return input_text


user_input = get_text()

if user_input:
    output = chain.run(input=user_input)
    df = pd.DataFrame(output).dropna(axis=1).iloc[0]

    with st.chat_message("user"):
        st.write("Does the below look correct? If so press submit")
        st.write("If changes are needed, please make them before submitting.")

        st.data_editor(df)

        with st.form('confirmationForm'):
            st.text_input(value=df['business_name'], label='Business Name')
            st.text_input(value=df['event_type'], label='Experience Type')
            st.number_input(value=df['event_price'], label='Experience Price', min_value=0)

            submit = st.form_submit_button('Submit')


