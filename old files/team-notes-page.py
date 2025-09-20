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
players = fetch_table_data('players')
players.set_index('id',inplace=True)
coaches = fetch_table_data('coaches')
coaches.set_index('id',inplace=True)
notes = fetch_table_data('notes')
notes.set_index('id',inplace=True)
team_notes = fetch_table_data('team_notes')
team_notes.set_index('id',inplace=True)

#%% View Team Notes

st.title('Team Notes')

# Merge coach names onto table
team_notes_display = team_notes.merge(coaches, left_on='coach_id', right_index=True, how='left')

team_notes_display = team_notes_display.drop(['coach_id'], axis=1)

team_notes_display.rename(columns={
    'name': 'Coach',
    'note': 'Note',
    'date': 'Date'
}, inplace=True)

st.dataframe(team_notes_display[['Date','Coach','Note']],hide_index=True)
