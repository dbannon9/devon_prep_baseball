#%% Imports

import pandas as pd
import numpy as np
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
video = fetch_table_data('video')
video.set_index('id',inplace=True)
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_hitting.set_index('id',inplace=True)
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
rapsodo_pitching.set_index('id',inplace=True)

#%% Data Adjustments

# define average()
def average(series):
    return sum(series) / len(series) if series else 0

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

# create dupe id
players['player_id'] = players.index

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

## Display Rapsodo Stats

# merge player_id onto rapsodo data
raphit = rapsodo_hitting.merge(players,left_on='Player ID', right_on='rapsodo_id', how='left')
player_raphit = raphit[raphit['player_id']==player_select][raphit['ExitVelocity']!="-"]

# generate stats
if len(player_raphit) < 1:
    st.write('No Rapsodo Hitting Stats Available')
else:
    st.subheader("Rapsodo Hitting Stats")
    ev_max = max(pd.to_numeric(player_raphit['ExitVelocity'],errors='coerce'))
    ev_avg = round(pd.to_numeric(player_raphit['ExitVelocity'],errors='coerce').mean(),1)
    ev_90 = round(np.percentile(pd.to_numeric(player_raphit['ExitVelocity'],errors='coerce').dropna(), 90),1)
    st.write(f"""Max EV: {ev_max}
             90th pct EV: {ev_90}
             Average EV: {ev_avg}""")

## Display Coach Notes

st.subheader("Coach Notes")
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

st.dataframe(notes_table[['Player','Type','Date','Coach','Note']],hide_index=True)

# Get video rows for this player, sorted by most recent
def display_video():
    player_name = player_options[player_select]  # Get the player name from player_options
    player_videos = video[video['player_id'] == player_select]
    for index, row in player_videos.iterrows():
        st.write(f"{row['date']} - {player_name} - {row['speed']} - {row['pitch_type']}")
        st.video(row['url'])

st.subheader("Video:")
display_video()

# %%
