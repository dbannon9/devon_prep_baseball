#%% Imports

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, time
import math
from decimal import Decimal
import os
from st_supabase_connection import SupabaseConnection

#%% Connect to Supabase

# Use st.secrets to load the URL and key from secrets.toml
# supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
# supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]

db = st.connection("supabase",type=SupabaseConnection)

# # Create the connection object using SupabaseConnection
# db = create_client(supabase_url, supabase_key)

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

    # Set index
    df.set_index('id', inplace=True)

    return df

# Fetch data from all tables, then align id to supabase index
players = fetch_table_data('players')
coaches = fetch_table_data('coaches')
notes = fetch_table_data('notes')
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_pitching = fetch_table_data('rapsodo_pitching')

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

# Assign types of notes
note_types = ['Fielder','Hitter','Pitcher']

# create currentplayers table
currentplayers = players_show.query('active == True')

# Prepare dropdown options
player_options = players_show['full_name'].to_dict()
coach_options = coaches['name'].to_dict()

#%% Player Page

st.title('Player Summary Page')

player_select = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id])

## Display Rapsodo Stats

# merge player_id onto rapsodo data
players_reset = players.reset_index()  # brings 'id' back as a column
raphit = rapsodo_hitting.merge(players_reset,left_on='Player ID', right_on='rapsodo_id', how='left').rename(columns = {'id':'player_id'})
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