#%% Imports

import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import numpy as np
from datetime import date, time, datetime
import math
from decimal import Decimal
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

#%% Connect to Supabase
db = st.connection("supabase",type=SupabaseConnection)

#%% Data Retrieval

# Function to fetch data from any table
def fetch_table_data(table_name):
    response = db.client.table(table_name).select("*").execute()

    # Supabase v2 client: actual rows are in response.data
    data = response.data
    if not data:
        st.warning(f"No data returned from table '{table_name}'.")
        return pd.DataFrame()

    # Normalize into DataFrame
    df = pd.DataFrame(data)

   # Set index to 'id' if it exists, otherwise 'uuid'
    if 'id' in df.columns:
        df.set_index('id', inplace=True)
    elif 'uuid' in df.columns:
        df.set_index('uuid', inplace=True)
    return df

# Fetch data from all tables, then align id to supabase index
players = fetch_table_data('players')
coaches = fetch_table_data('coaches')
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
swings = fetch_table_data('swings')

#%% Data Adjustments

# assign class levels to index of years
classdict = {
        0: "Grad",
        1: "Senior",
        2: "Junior",
        3: "Sophomore",
        4: "Freshman",
        5: "Middle"
}

# create the display version of players
players_show = players.copy()

# assign class year names to each player based on graduation year
def classdef(df):
    class_years = []
    for grad_year in df['grad_year']:
        if isinstance(grad_year, Decimal):
            grad_year = int(grad_year)
        # Calculate difference in years between grad date and today
        years_diff = math.ceil((date(grad_year, 9, 1) - date.today()).days / 365)
        # Cap within 0–5
        if years_diff >= 5:
            years_diff = 5
        elif years_diff < 1:
            years_diff = 0
        # Look up label from classdict
        class_year = classdict.get(years_diff, "Unknown")
        class_years.append(class_year)
    # Assign back to the DataFrame
    df['class'] = class_years

# Run the function on your display DataFrame
classdef(players_show)

# Create Players Full Name Column
players_show['full_name'] = players_show['first_name'] + ' ' + players_show['last_name']

# assign player active status by class
active_classes = ['Freshman','Sophomore','Junior','Senior']
players_show['active'] = players_show['class'].isin(active_classes)

# create currentplayers table
currentplayers = players_show.query('active == True')

# Prepare dropdown options
player_options = players_show['full_name'].to_dict()
active_player_options = currentplayers['full_name'].to_dict()
coach_options = coaches['name'].to_dict()

#%% Form
st.title("Plate Discipline Tracking")
handednesses = ["Right","Left"]
zones = [None,"Heart","Shadow","Chase","Waste"]
east_west_zones = [None,"Waste In","Shadow In","Heart","Shadow Out","Waste Out"]
north_south_zones = [None,"Waste Up","Shadow Up","Heart","Shadow Down","Waste Down"]
pitch_type = [None,"Fastball","Breaking Ball","Offspeed"]
decisions = [None,"Take","Swing"]
take_outcomes = [None,"Ball","Strike"]
swing_outcomes = [None,"Whiff","Foul","Weak Contact","Solid Contact"]
batted_ball_types = [None,"Grounder", "Line Drive", "Fly Ball", "Pop Up"]

# Hitter & handedness outside of form so it doesnt clear
pa_hitter = st.selectbox("Player", options=list(active_player_options.keys()), format_func=lambda id: active_player_options[id])
pitcher_handedness = st.selectbox("Pitcher Handedness",handednesses)
st.divider()
pitch_type = st.selectbox("Pitch Type",pitch_type)
north_south_location = st.selectbox("Up/Down Location",north_south_zones)
east_west_location = st.selectbox("In/Out Location",east_west_zones)
st.divider()
decision = st.selectbox("Decision",decisions)
if decision == "Take":
    take_outcome = st.selectbox("Take Outcome",take_outcomes)
elif decision == "Swing":
    swing_outcome = st.selectbox("Swing Outcome",swing_outcomes)
    if swing_outcome in ["Weak Contact", "Solid Contact"]:
        batted_ball_type = st.selectbox("Batted Ball Type",batted_ball_types)

st.divider()
submit = st.button("Submit Pitch")

