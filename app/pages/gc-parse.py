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
import re as re

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

#%% Testing


# PA Results
gc_pa_results = ['Strikeout','Walk','Single','Double','Triple','Home Run','Fly Out','Ground Out','Line Out','Fielder''s Choice','Runner out','Double Play','Triple Play','Pop Out','Hit By Pitch','Catcher''s Interference','Intentional Walk','Error']
gc_pitch_results = ['Strike 1 looking','Strike 1 swinging','Strike 2 looking','Strike 2 swinging','Strike 3 looking','Strike 3 swinging','Foul','Ball 1','Ball 2','Ball 3','Ball 4','In play']

txtfile = st.file_uploader("Dump GC Text File Here", accept_multiple_files=False)

txtdata = pd.read_csv(txtfile, header=None,names=['text']) if txtfile is not None else pd.DataFrame()

if not txtdata.empty:
    # Team Assignments
    dp_col, other_col = st.columns(2,gap="small")
    with dp_col:
        dp_team_abbrev = st.text_input("Input Opponent's GC Abbreviation",value='DVNP')
    with other_col:
        other_team_abbrev = st.text_input("Input Opponent's GC Abbreviation")

    txtdata['is_inning_change'] = txtdata['text'].str.contains(r'Top \d|Bottom \d',regex=True,na=False)
    txtdata['is_pa_result'] = txtdata['text'].isin(gc_pa_results)
    txtdata['is_out_change'] = txtdata['text'].str.contains(r'\d Out')
    pattern = '|'.join(gc_pitch_results)
    txtdata['is_pitch_sequence'] = txtdata['text'].str.findall(pattern).str.len() > 0
    txtdata['is_score_change'] = txtdata['text'].str.contains(dp_team_abbrev)
    cols = ['is_inning_change','is_pa_result','is_out_change','is_pitch_sequence','is_score_change']
    txtdata['is_outcome_string'] = ~txtdata[cols].any(axis=1)

    pitch_sequences = txtdata[txtdata['is_pitch_sequence']]
    pitch_sequences