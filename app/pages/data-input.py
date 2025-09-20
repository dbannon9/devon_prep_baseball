#%% Imports

import pandas as pd
import streamlit as st
import numpy as np
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import Client, create_client


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

# Fetch data from tables, then align id to supabase index
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
rapsodo_pitching.set_index('id',inplace=True)
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_hitting.set_index('id',inplace=True)
swings = fetch_table_data('swings')
swings.set_index('id',inplace=True) 

#%% .csv Data Dump

st.title("Rapsodo Data Input")
new_file = st.file_uploader("Dump Diamond Kinetics .csv File, or Rapsodo 'pitchinggroup' or 'hittinggroup' File Here",type='csv')
if new_file:
    file_df = pd.read_csv(new_file)
    # dk, raposdo hitting, or rapsodo pitching?
    file_cols = file_df.columns

    # file_df.replace("-", np.nan, inplace=True)
    file_df['Date'] = pd.to_datetime(file_df['Date']).dt.strftime('%Y-%m-%d')
    
    # upload button
if new_file:
    file_df = pd.read_csv(new_file)
    file_cols = file_df.columns

    # Determine file type immediately
    if "Pitch ID" in file_cols:
        file_type = "rapsodo_pitching"
    elif "HitID" in file_cols:
        file_type = "rapsodo_hitting"
    elif "user.battingOrientation" in file_cols:
        file_type = "dk_hitting"
        file_df = file_df.iloc[2:, 15:]  # skip first 2 rows, drop first 15 columns
        file_df.reset_index(drop=True, inplace=True)
    else:
        file_type = None
        st.error("Unrecognized file type!")

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
                response = supabase.table("rapsodo_pitching").insert(pitch_upload).execute()
                st.session_state.form_submitted = True
                st.success("Rapsodo Pitching Data Successfully Uploaded")

        elif file_type == "rapsodo_hitting":
            hit_upload = file_df[~file_df['HitID'].isin(rapsodo_hitting['HitID'])]
            if len(hit_upload) == 0:
                st.success("Rapsodo Hitting Data is Up To Date")
            else:
                hit_upload = hit_upload.to_dict(orient="records")
                response = supabase.table("rapsodo_hitting").insert(hit_upload).execute()
                st.session_state.form_submitted = True
                st.success("Rapsodo Hitting Data Successfully Uploaded")

        elif file_type == "dk_hitting":
            dk_upload = file_df[~file_df['UUID'].isin(swings['uuid'])]
            if len(dk_upload) == 0:
                st.success("Diamond Kinetics Hitting Data is Up To Date")
            response = supabase.table("swings").insert(dk_upload).execute()
            st.session_state.form_submitted = True
            st.success("Diamond Kinetics Data Successfully Uploaded")

