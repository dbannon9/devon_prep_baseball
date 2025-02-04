#%% Imports

import pandas as pd
import streamlit as st
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client

#%% Connect to Supabase

# Use st.secrets to load the URL and key from secrets.toml
supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]

# get secrets from toml
supabase: Client = create_client(supabase_url, supabase_key)

# Create the connection object using SupabaseConnection
db = create_client(supabase_url, supabase_key)

#%% Data Retrieval

# Function to fetch data from any table
def fetch_table_data(table_name):
    # Execute the SQL query
    df = supabase.table(f"{table_name}").select("*").execute().data
    
    # Convert the fetched data into a pandas DataFrame
    return pd.DataFrame(df)

# Fetch data from all tables, then align id to supabase index
practice_plans = fetch_table_data('practice_plans')
practice_plans.set_index('id',inplace=True)
practice_event = fetch_table_data('practice_event')
practice_event.set_index('id',inplace=True)

#%% Data Definitions

date_str = ""
event_1_start_time = ""
event_1_end_time = ""
event_1_name = ""
event_1_notes = ""
event_2_start_time = ""
event_2_end_time = ""
event_2_name = ""
event_2_notes = ""
event_3_start_time = ""
event_3_end_time = ""
event_3_name = ""
event_3_notes = ""
event_4_start_time = ""
event_4_end_time = ""
event_4_name = ""
event_4_notes = ""

#%% Input Practice Plans

st.title('Create New Practice Plan')
practice_plans_date = st.date_input("Practice Date", value=date.today())  # Default value to today's date
date_events = practice_event.query(f"date == '{practice_plans_date.isoformat()}'").sort_values(by="start_time",ascending=True)

st.header('Existing Events:')
edit_toggle = st.toggle('Edit?')
if edit_toggle:
    events_update = st.data_editor(date_events)
    save = st.button("Save")
    if save:
        for idx, row in events_update.iterrows():
            event_id = row.name  # This accesses the index (which is 'id' in your case)
            try:
                response = supabase.table("practice_event").update(row.to_dict()).eq('id', event_id).execute()
            except Exception as e:
                st.error(f"Supabase Error: {e}")    
        # Mark the form as submitted
        st.session_state.form_submitted = True

        # Display success message
        st.success("Data successfully saved")
else:
    st.dataframe(date_events, hide_index=True)


# # Input fields for the first event
# event_1_name = st.text_input("First Event Name")  # Name of the first event
# event_1_notes = st.text_input("Describe the First Event")  # Notes about the first event
# event_1_start_time = st.time_input("First Event Start Time")  # Start time of the first event
# event_1_end_time = st.time_input("First Event End Time")  # End time of the first event

# # Radio button for the second event
# second_event = st.radio("Second Event?", ["No", "Yes"], horizontal=True)

# # Show the second event inputs if "Yes" is selected
# if second_event == "Yes":
#     event_2_name = st.text_input("Second Event Name")  # Name of the second event
#     event_2_notes = st.text_input("Describe the Second Event")  # Notes about the second event
#     event_2_start_time = st.time_input("Second Event Start Time")  # Start time of the second event
#     event_2_end_time = st.time_input("Second Event End Time")  # End time of the second event
    
#     # Radio button for the third event
#     third_event = st.radio("Third Event?", ["No", "Yes"], horizontal=True)
#     if third_event == "Yes":
#         event_3_name = st.text_input("Third Event Name")  # Name of the Third event
#         event_3_notes = st.text_input("Describe the Third Event")  # Notes about the Third event
#         event_3_start_time = st.time_input("Third Event Start Time")  # Start time of the Third event
#         event_3_end_time = st.time_input("Third Event End Time")  # End time of the Third event

#         # Radio button for the Fourth event
#         Fourth_event = st.radio("Fourth Event?", ["No", "Yes"], horizontal=True)
#         if Fourth_event == "Yes":
#             event_4_name = st.text_input("Fourth Event Name")  # Name of the Fourth event
#             event_4_notes = st.text_input("Describe the Fourth Event")  # Notes about the Fourth event
#             event_4_start_time = st.time_input("Fourth Event Start Time")  # Start time of the Fourth event
#             event_4_end_time = st.time_input("Fourth Event End Time")  # End time of the Fourth event

# # Convert the date object to ISO 8601 string format
# date_str = practice_plans_date.isoformat()  # Converts the date object to 'YYYY-MM-DD'

# new_practice_plan = {
#     'date': date_str,
#     'coach_quote': coach_quote,
#     'event_1_start_time': event_1_start_time.strftime('%H:%M') if event_1_start_time else None,
#     'event_1_end_time': event_1_end_time.strftime('%H:%M') if event_1_end_time else None,
#     'event_1_name': event_1_name,
#     'event_1_notes': event_1_notes,
#     'event_2_start_time': event_2_start_time.strftime('%H:%M') if event_2_start_time else None,
#     'event_2_end_time': event_2_end_time.strftime('%H:%M') if event_2_end_time else None,
#     'event_2_name': event_2_name,
#     'event_2_notes': event_2_notes,
#     'event_3_start_time': event_3_start_time.strftime('%H:%M') if event_3_start_time else None,
#     'event_3_end_time': event_3_end_time.strftime('%H:%M') if event_3_end_time else None,
#     'event_3_name': event_3_name,
#     'event_3_notes': event_3_notes,
#     'event_4_start_time': event_4_start_time.strftime('%H:%M') if event_4_start_time else None,
#     'event_4_end_time': event_4_end_time.strftime('%H:%M') if event_4_end_time else None,
#     'event_4_name': event_4_name,
#     'event_4_notes': event_4_notes
# }

# practice_submit = st.button("Submit Practice Plan")

# if practice_submit:
#     response = supabase.table("practice_plans").insert(new_practice_plan).execute()
#     st.success("Practice Plan Submitted Successfully")

# # Push using insert function

# # Mark as complete:
