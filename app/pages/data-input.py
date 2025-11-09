#%% Imports

import pandas as pd
import streamlit as st
import numpy as np
from datetime import date, time
import math
from decimal import Decimal
import os
from st_supabase_connection import SupabaseConnection


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
dk_curves = fetch_table_data('dk_curves')

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

#%% .csv Data Dump

st.title("Data Input")
new_file = st.file_uploader("Dump Diamond Kinetics .csv File, or Rapsodo 'pitchinggroup' or 'hittinggroup' File Here",type="csv")

if new_file is not None:
    file_df=pd.read_csv(new_file)
    file_df.replace("-", None, inplace=True)
    file_cols = file_df.columns
    # Determine file type
    if "Pitch ID" in file_cols:
        file_type = "rapsodo_pitching"
    elif "HitID" in file_cols:
        file_type = "rapsodo_hitting"
    elif "user.battingOrientation" in file_cols:
        file_type = "dk_hitting"
        file_df = pd.read_csv(new_file, header=3)
        file_df = file_df.iloc[:, 15:]  # drop first 15 columns
        file_df.reset_index(drop=True, inplace=True)
    else:
        file_type = None
        st.error("Unrecognized file type.")

    # Standardize Date column if it exists
    if "Date" in file_cols:
        file_df['Date'] = pd.to_datetime(file_df['Date']).dt.strftime('%Y-%m-%d')

    # Upload button
    upload = st.button("Upload Data")
    if upload and file_type:
        if file_type == "rapsodo_pitching":
            pitch_upload = file_df[~file_df['Pitch ID'].isin(rapsodo_pitching['Pitch ID'])]
            if len(pitch_upload) == 0:
                st.success("Rapsodo Pitching Data is Up To Date")
            else:
                pitch_upload = pitch_upload.to_dict(orient="records")
                response = db.table("rapsodo_pitching").insert(pitch_upload).execute()
                st.session_state.form_submitted = True
                st.success("Rapsodo Pitching Data Successfully Uploaded")

        elif file_type == "rapsodo_hitting":
            hit_upload = file_df[~file_df['HitID'].isin(rapsodo_hitting['HitID'])]
            if len(hit_upload) == 0:
                st.success("Rapsodo Hitting Data is Up To Date")
            else:
                hit_upload = hit_upload.to_dict(orient="records")
                response = db.table("rapsodo_hitting").insert(hit_upload).execute()
                st.session_state.form_submitted = True
                st.success("Rapsodo Hitting Data Successfully Uploaded")

        elif file_type == "dk_hitting":
            dk_upload = file_df[~file_df['UUID'].isin(swings['uuid'])]
            if len(dk_upload) == 0:
                st.success("Diamond Kinetics Hitting Data is Up To Date")
            response = db.table("swings").insert(dk_upload).execute()
            st.session_state.form_submitted = True
            st.success("Diamond Kinetics Data Successfully Uploaded")