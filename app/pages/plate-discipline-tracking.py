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
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
swings = fetch_table_data('swings')
plate_discipline = fetch_table_data('plate_discipline')

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

#%% Rerun logic:

if st.session_state.get("reset_pitch_fields", False):

    for key in [
        "pitch_type", "v_location", "h_location",
        "decision", "take_outcome", "swing_outcome", "batted_ball_type"
    ]:
        if key in st.session_state:
            st.session_state[key] = None

    # Clear the flag
    st.session_state["reset_pitch_fields"] = False


#%% Form
st.title("Plate Discipline Tracking")
handednesses = ["Right","Left"]
zones = ["Heart","Shadow","Chase","Waste"]
h_zones = ["Waste In","Shadow In","Heart","Shadow Out","Waste Out"]
v_zones = ["Waste Up","Shadow Up","Heart","Shadow Down","Waste Down"]
pitch_type = ["Fastball","Breaking Ball","Offspeed"]
decisions = ["Take","Swing"]
outcomes = ["Ball","Called Strike","Whiff","Foul","Grounder", "Line Drive", "Fly Ball", "Pop Up"]
take_outcomes = ["Ball","Called Strike"]
swing_outcomes = ["Whiff","Foul","Grounder", "Line Drive", "Fly Ball", "Pop Up"]
contact_outcomes = ["Grounder", "Line Drive", "Fly Ball", "Pop Up"]
contact_qualities = ["Soft","Medium","Hard"]

# form
date_col, hitter_col, handedness_col = st.columns(3,gap="small")
with date_col:
    st.subheader("Today's Date",divider="yellow")
    pa_date = st.date_input("Today's Date", value=date.today(),label_visibility="collapsed")
with hitter_col:
    st.subheader("Hitter",divider="yellow")
    pa_hitter = st.selectbox("Hitter",options=list(active_player_options.keys()), format_func=lambda id: active_player_options[id],label_visibility="collapsed")
with handedness_col:
    st.subheader("Pitcher Handedness",divider="yellow")
    pitcher_handedness = st.selectbox("Pitcher Handedness",options=handednesses,index=None,label_visibility="collapsed")
st.divider()
type_col, v_loc_col, h_loc_col = st.columns(3,gap="small")
with type_col:
    st.subheader("Pitch Type",divider="yellow")
    pitch_type_select = st.radio("**Pitch Type**", pitch_type, key="pitch_type",index=None,label_visibility="collapsed")
with v_loc_col:
    st.subheader("Up/Down Location",divider="yellow")
    v_location = st.radio("**Up/Down Location**", v_zones, key="v_location",index=None,label_visibility="collapsed")
with h_loc_col:
    st.subheader("In/Out Location",divider="yellow")
    h_location = st.radio("**In/Out Location**", h_zones, key="h_location",index=None,label_visibility="collapsed")
st.divider()
outcome_col, contact_quality_col, empty_col = st.columns(3,gap="small")
with outcome_col:
    st.subheader("Outcome",divider="yellow")
    outcome = st.radio("**Outcome**", outcomes, key="outcome",index=None,label_visibility="collapsed")
with contact_quality_col:
    if outcome in contact_outcomes:
        st.subheader("Contact Quality",divider="yellow")
        contact_quality = st.radio("**Contact Quality**",options=contact_qualities, key="contact_quality",index=None,label_visibility="collapsed")
    else:
        ""
with empty_col:
    ""
decision = "Take" if outcome in take_outcomes else "Swing"
made_contact = True if outcome in contact_outcomes else False

pa_date_iso = pa_date.isoformat()

st.divider()
submit = st.button("Submit Pitch")

if submit:
    new_pitch = {
        'date': pa_date_iso,  # Use the string version of the date
        'player_id': pa_hitter,
        'pitcher_handedness': pitcher_handedness,
        'pitch_type': pitch_type_select,
        'v_location': v_location,
        'h_location': h_location,
        'decision': decision,
        'outcome': outcome,
        'made_contact': made_contact,
        'contact_quality': contact_quality if outcome in contact_outcomes else None
    }
    response = db.client.table("plate_discipline").insert(new_pitch).execute()
    st.success("Pitch Submitted Successfully")
    st.session_state["reset_pitch_fields"] = True
    st.rerun()
