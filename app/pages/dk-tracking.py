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
dk_sessions = fetch_table_data('dk_sessions')

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


#%% Get recent data from table
today_str = date.today().isoformat()
dk_session_today = dk_sessions["session_date"] == today_str

if len(dk_session_today)==0:
    max_swing_today = 0
else:
    max_swing_today = (dk_sessions.loc[
        dk_session_today,
        "swing_number"
    ]
    ).max()
    last_bat_length = (
        dk_session_today
        .sort_values("created_at")
        .iloc[-1]["bat_length"]
    )

#%% Form
st.title("DK Session Tracking")

# form
session_date = st.date_input("Session Date", value=date.today())
hitter = st.selectbox("Hitter", options=list(active_player_options.keys()), format_func=lambda id: active_player_options[id])
bat_length = st.number_input("Bat Length",value=last_bat_length)
st.markdown(f"_Most recent swing number today: ***{max_swing_today}***_")
start_swing = st.number_input("Start Swing Number",value=max_swing_today+1)
end_swing = st.number_input("End Swing Number",value=max_swing_today+5)
session_date_iso = session_date.isoformat()
submit = st.button("Submit Swings")

if submit:

    new_rows = [
        {
            "session_date": session_date_iso,
            "swing_number": swing_num,
            "player_id": hitter
        }
    for swing_num in range(start_swing, end_swing + 1)
    ]
    response = db.client.table("dk_sessions").insert(new_rows).execute()
    st.success(f"Inserted swings {start_swing}–{end_swing}")
    st.rerun()
