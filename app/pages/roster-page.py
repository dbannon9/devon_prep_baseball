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

#%% Roster Toggles
st.title("Devon Prep Baseball Roster")
ptoggle = st.toggle('Pitchers?')
if ptoggle:
    fplayers = players.query('pitcher == True & active == True')[['first_name','last_name','class']]
else:
    fplayers = players[['first_name','last_name','class','pos_1','pos_2','pos_3']].fillna('')

st.dataframe(fplayers,hide_index=True)