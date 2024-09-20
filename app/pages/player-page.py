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
players = fetch_table_data('players')
players.set_index('id',inplace=True)
coaches = fetch_table_data('coaches')
coaches.set_index('id',inplace=True)
notes = fetch_table_data('notes')
notes.set_index('id',inplace=True)

#%% Data Adjustments

# assign class levels to index of years
classdict = {
        0: "Middle",
        1: "Senior",
        2: "Junior",
        3: "Sophomore",
        4: "Freshman",
        5: "Grad"
}

# assign class year names to each player based on graduation year
def classdef(thing):
    class_years = []
    for thing in players['grad_year']:
        if isinstance(thing, Decimal):
            thing = int(thing)
        years_diff = math.ceil((date(thing, 9, 1) - date.today()).days / 365)
        if years_diff >= 5:
            return 5
        elif years_diff <1:
            return 0
        class_year = classdict.get(years_diff)
        class_years.append(class_year)
    players['class'] = class_years
classdef(players['grad_year'])

# Create Players Full Name Column
players['full_name'] = players['first_name'] + ' ' + players['last_name']

# assign player active status by class
active_classes = ['Freshman','Sophomore','Junior','Senior']
players['active'] = players['class'].isin(active_classes)

# Assign types of notes
note_types = ['Fielder','Hitter','Pitcher']

# create currentplayers table
currentplayers = players.query('active == True')

# Prepare dropdown options
player_options = players['full_name'].to_dict()
coach_options = coaches['name'].to_dict()

#%% Player Page

st.title('Player Summary Page')

player_select = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id])
type_select = st.multiselect("Type",options=note_types,default=note_types)

# Merge coach names onto table
notes_display = notes.merge(coaches, left_on='coach_id', right_index=True, how='left').merge(players,left_on='player_id',right_index=True,how='left')

notes_display = notes_display.drop(['coach_id'], axis=1)

filtered_notes = notes_display[notes_display['player_id'] == player_select]

notes_table = filtered_notes[filtered_notes['type'].isin(type_select)]

notes_table.rename(columns={
    'full_name': 'Player',
    'type': 'Type',
    'name': 'Coach',
    'note': 'Note',
    'date': 'Date'
}, inplace=True)

# st.table(notes_table[['Player','Type','Date','Coach','Note']])

st.dataframe(notes_table[['Player','Type','Date','Coach','Note']],hide_index=True)

# query("player_id == player_select")