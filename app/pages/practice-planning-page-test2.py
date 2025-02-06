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

locations = [
    "Whole Field",
    "Infield",
    "Outfield",
    "Bullpen",
    "Indoor (Full)",
    "Indoor (Half)"
]

#%% Page Header

st.title('Create New Practice Plan')
practice_plans_date = st.date_input("Practice Date", value=date.today())  # Default value to today's date

#%% Display Existing Practice Plans

date_events = practice_event.query(f"date == '{practice_plans_date.isoformat()}'").sort_values(by="start_time",ascending=True)

st.header('Existing Events:')

if len(date_events) < 1:
    st.write("No Events for the Selected Date")
else:
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

            # Display success message
            st.success("Data successfully saved")
    
    else:
        date_events_show = date_events.copy()
        date_events_show.rename(columns={
                                    'start_time': 'Start',
                                    'end_time': 'End',
                                    'name': 'Name',
                                    'location': 'Location',
                                    'notes': 'Notes',
                                    'date': 'Date'
                                    }, inplace=True)
        st.dataframe(date_events_show, hide_index=True)


#%% Input New Practice Events

st.header('Input New Practice Events')

with st.form(key='Input New Practice Event',clear_on_submit=True):
    event_name = st.text_input("Event Name")
    event_desc = st.text_input("Event Description")
    event_start = st.time_input("Start Time")
    event_end = st.time_input("End Time")
    event_location = st.selectbox("Location", options=locations)
    event_submit = st.form_submit_button(label="Submit Event")

# When form is submitted
if event_submit:

    # Create new note dictionary with IDs
    new_event = {
        'start_time': event_start.strftime('%H:%M'),
        'end_time': event_end.strftime('%H:%M'),
        'name': event_name,
        'location': event_location,
        'notes': event_desc,
        'date': practice_plans_date.isoformat()
    }

    # Push using insert function
    response = supabase.table("practice_event").insert(new_event).execute()

    # Mark the form as submitted
    st.session_state.form_submitted = True

    # Display success message
    st.success("Event submitted successfully")

