#%% Imports

import pandas as pd
import numpy as np
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
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_hitting.set_index('id',inplace=True)
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
rapsodo_pitching.set_index('id',inplace=True)

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

#%% Home Page
 
st.title("Devon Prep Baseball")

#%% Creating Rapsodo Leaderboards

## Hitting

# merge for id purposes
raphit = rapsodo_hitting.merge(players_show,left_on='Player ID', right_on='rapsodo_id', how='left')
raphit['ExitVelocity'] = pd.to_numeric(raphit['ExitVelocity'], errors='coerce')[raphit['ExitVelocity']!="-"]

# group by id
raphit_group = raphit.groupby('rapsodo_id').agg(
    ExitVelocity_max=('ExitVelocity', 'max'),
    ExitVelocity_avg=('ExitVelocity', 'mean'),
    ExitVelocity_90th_percentile=('ExitVelocity', lambda x: np.percentile(x, 90))
).reset_index()

# join full_name back on
raphit_group = raphit_group.merge(
    players_show[['rapsodo_id', 'full_name']], 
    on='rapsodo_id', 
    how='left'
)

raphit_group.rename(columns={
    'full_name': 'Player',
    'ExitVelocity_max': 'Max EV',
    'ExitVelocity_avg': 'Average EV',
    'ExitVelocity_90th_percentile': '90th pct EV',
}, inplace=True)

raphit_group.sort_values(by='Average EV', ascending=False, inplace=True)

st.subheader("Rapsodo Leaderboard")
st.dataframe(raphit_group[['Player','Average EV','90th pct EV','Max EV']],
             hide_index=True,
             column_config={
                 "Max EV": st.column_config.NumberColumn(format="%.1f"),
                 "Average EV": st.column_config.NumberColumn(format="%.1f"),
                 "90th pct EV": st.column_config.NumberColumn(format="%.1f")
                })

#%% Roster Toggles

st.subheader("Roster & Positions")
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
    players_update = st.data_editor(players)
    save = st.button("Save")
    if save:
        for idx, row in players_update.iterrows():
            player_id = row.name  # This accesses the index (which is 'id' in your case)
            response = supabase.table("players").update(row.to_dict()).eq('id', player_id).execute()
    
        # Mark the form as submitted
        st.session_state.form_submitted = True

        # Display success message
        st.success("Data successfully saved")


else:
    st.dataframe(fplayers,hide_index=True)
