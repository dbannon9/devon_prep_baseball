#%% Imports

import pandas as pd
import streamlit as st
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client

#%% create connection with supabase

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
schedule = fetch_table_data('schedule')
schedule.set_index('id',inplace=True)

#%% Schedule Page

st.title('Schedule')

schedule.rename(columns={
    'event_type': 'Event Type',
    'date': 'Date',
    'time': 'Time',
    'opponent': 'Opponent',
    'home_road': 'Home/Road',
    'conference': 'Conference Game',
    'teams': 'Teams',
    'location': 'Location'
}, inplace=True)

st.dataframe(schedule,hide_index=True)
