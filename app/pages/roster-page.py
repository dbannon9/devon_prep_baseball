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

#create the display version of players
players_show = players.copy()

# assign class year names to each player based on graduation year
def classdef(thing):
    class_years = []
    for thing in players_show['grad_year']:
        if isinstance(thing, Decimal):
            thing = int(thing)
        years_diff = math.ceil((date(thing, 9, 1) - date.today()).days / 365)
        if years_diff >= 5:
            return 5
        elif years_diff <1:
            return 0
        class_year = classdict.get(years_diff)
        class_years.append(class_year)
    players_show['class'] = class_years
classdef(players_show['grad_year'])

# Create Players Full Name Column
players_show['full_name'] = players_show['first_name'] + ' ' + players_show['last_name']

# assign player active status by class
active_classes = ['Freshman','Sophomore','Junior','Senior']
players_show['active'] = players_show['class'].isin(active_classes)

# Assign types of notes
note_types = ['Fielder','Hitter','Pitcher']

# create currentplayers table
currentplayers = players_show.query('active == True')

# Prepare dropdown options
player_options = players_show['full_name'].to_dict()
coach_options = coaches['name'].to_dict()

#%% Roster Toggles
st.title("Devon Prep Baseball Roster")
edit_toggle = st.toggle('Edit?')
ptoggle = st.toggle('Pitchers?')
if ptoggle:
    fplayers = players_show.query('pitcher == True & active == True')[['first_name','last_name','class']]
    fplayers.rename(columns={
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'class': 'Grade Level'
        }, inplace=True)
else:
    fplayers = players_show[['first_name','last_name','class','pos_1','pos_2','pos_3']].fillna('')
    fplayers.rename(columns={
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'class': 'Grade Level',
        'pos_1': 'Primary Position',
        'pos_2': 'Secondary Position',
        'pos_3': 'Tertiary Position'
    }, inplace=True)

if edit_toggle:
    st.data_editor(players)
    save = st.button("Save")
    if save:
        try:

            players_update = players.to_dict(orient="records")

            response = supabase.table("players").update(players_update).eq('id',players['id']).execute()
        
            # Mark the form as submitted
            st.session_state.form_submitted = True

            # Display success message
            st.success("Data successfully saved")
        except Exception as e:
            st.write(e)


else:
    st.dataframe(fplayers,hide_index=True)