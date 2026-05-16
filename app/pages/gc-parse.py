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

# Fetch data from all tables
players = fetch_table_data('players')
games = fetch_table_data('games')
plate_appearances = fetch_table_data('plate_appearances')

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
txtdata = []
gc_pa_results = ['Strikeout','Walk','Single','Double','Triple','Home Run','Fly Out','Ground Out','Line Out','Fielder''s Choice','Runner Out','Double Play','Triple Play','Pop Out','Hit By Pitch','Catcher''s Interference','Intentional Walk','Error']
gc_pitch_results = ['Strike 1 looking','Strike 1 swinging','Strike 2 looking','Strike 2 swinging','Strike 3 looking','Strike 3 swinging','Foul','Ball 1','Ball 2','Ball 3','Ball 4','In play']
devon_teams = ['Varsity','Junior Varsity','Freshman']
dp_team_abbrev = 'DVNP'
innings_sequence = ['Top 1st', 'Bottom 1st', 'Top 2nd', 'Bottom 2nd', 'Top 3rd', 'Bottom 3rd', 'Top 4th', 'Bottom 4th', 'Top 5th', 'Bottom 5th', 'Top 6th', 'Bottom 6th', 'Top 7th', 'Bottom 7th', 'Top 8th', 'Bottom 8th', 'Top 9th', 'Bottom 9th', 'Top 10th', 'Bottom 10th', 'Top 11th', 'Bottom 11th', 'Top 12th', 'Bottom 12th', 'Top 13th', 'Bottom 13th']
search_cols = ['gc_name_with_number_1','gc_name_with_number_2','gc_name_with_number_3','gc_name_full_1','gc_name_full_2','gc_name_full_3','gc_name_initial_1','gc_name_initial_2','gc_name_initial_3']
# THIS NEEDS FIXING # long_players_and_gc_names = players.melt(id_vars='id',value_vars=search_cols,value_name='gc_match')

txtfile = st.file_uploader("Dump GC Text File Here", accept_multiple_files=False)
if txtfile == '':
    txtfileparsed = txtfile.getvalue().decode("utf-8").splitlines()
    txtdata = pd.DataFrame(txtfile, columns=['text'])

if not txtdata.empty:
    # Team Assignments
    txtdata['is_inning_change'] = txtdata['text'].str.contains(r'Top \d|Bottom \d',regex=True,na=False)
    txtdata['is_pa_result'] = txtdata['text'].isin(gc_pa_results)
    txtdata['is_out_change'] = txtdata['text'].str.contains(r'\d Out')
    pattern = '|'.join(gc_pitch_results)
    txtdata['is_pitch_sequence'] = txtdata['text'].str.findall(pattern).str.len() > 0
    txtdata['is_score_change'] = txtdata['text'].str.contains(dp_team_abbrev)
    cols = ['is_inning_change','is_pa_result','is_out_change','is_pitch_sequence','is_score_change']
    txtdata['is_outcome_string'] = ~txtdata[cols].any(axis=1)
    
    # inning logic determining home team
    inning_changes = txtdata.loc[txtdata['is_inning_change'], 'text']
    first_inning_row = inning_changes.iloc[0]
    is_devon_home = (
        ('Bottom' in first_inning_row and 'Devon' in first_inning_row)
        or
        ('Top' in first_inning_row and 'Devon' not in first_inning_row)
    )

    dp_col, other_col = st.columns(2,gap="small")
    with dp_col:
        dp_team_name = st.selectbox("Input Devon's Team Name",options=devon_teams,value='Varsity')
        dp_team_abbrev = st.text_input("Input Devon's GC Abbreviation",value='DVNP')
        game_date = st.date_input("Input Game Date",value='today')
    with other_col:
        other_team_name = st.text_input("Input Opponent's Team Name")
        other_team_abbrev = st.text_input("Input Opponent's GC Abbreviation")
        default_venue = 'Devon Prep' if is_devon_home else other_team_name
        venue = st.text_input("Input Venue Name",value=default_venue)

    #%% Test Data stuff

    txtdata

    pitch_sequences = txtdata[txtdata['is_pitch_sequence']]
    pitch_sequences

    outcome_strings_and_sequences = txtdata[txtdata['is_outcome_string']|txtdata['is_pitch_sequence']]
    outcome_strings_and_sequences

    #%% Processing Data

    # submit
    submit = st.button("Process Data",disabled=True) #re-enable when ready
    if submit:
        new_game = {
            'date': game_date,  # Use the string version of the date
            'is_devon_home': is_devon_home,
            'opponent_name': other_team_name,
            'venue': venue,
        }
        response = db.client.table("games").insert(new_game).execute()
        game_id = response.select()
        parsed_pas = []
        parsed_pitches = []
        current_home_score = 0
        current_away_score = 0
        current_outs = 0
        current_bases = "---"

        outs_before = 0
        outs_after = 0
        i = 0
        r = len(txtdata)-1
        while r >= 0:
            row = txtdata.iloc[i]
            current_inning = innings_sequence[i]
            if row['is_inning_change']:
                i = i + 1
                outs_before = 0
                outs_after = 0
                continue
            if row['is_outcome_string']:
                if row['text'] != "Half-inning ended by out on the base paths.":                    
                    batter_match_text = None #ADD RESULTS STRING HERE
                    batter_matches = long_players_and_gc_names.loc[long_players_and_gc_names['gc_match']==batter_match_text,'id']
                    batter_match_id = batter_matches.iloc[0] if not batter_matches.empty else None
                    if batter_match_id == None:
                        batter_handedness = None
                    else:
                        batter_handedness = players.loc[players['id']==batter_match_id,'bats']
                    pitcher_match_text = None #ADD RESULTS STRING HERE
                    pitcher_matches = long_players_and_gc_names.loc[long_players_and_gc_names['gc_match']==pitcher_match_text,'id']
                    pitcher_match_id = pitcher_matches.iloc[0] if not pitcher_matches.empty else None
                    if pitcher_match_id == None:
                        pitcher_handedness = None
                    else:
                        pitcher_handedness = players.loc[players['id']==pitcher_match_id,'throws']
                    pa = {
                        'game_id': game_id,
                        'inning': current_inning,
                        'batter_id': batter_match_id,
                        'pitcher_id': pitcher_match_id,
                        'result': row['text'],
                    }