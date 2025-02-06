#%% Imports

import pandas as pd
import streamlit as st
import numpy as np
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

# Fetch data from tables, then align id to supabase index
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
rapsodo_pitching.set_index('id',inplace=True)
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_hitting.set_index('id',inplace=True)

#%% .csv Data Dump

st.title("Rapsodo Data Input")
new_file = st.file_uploader("Dump Rapsodo 'pitchinggroup' or 'hittinggroup' File Here",type='csv')
if new_file:
    file_df = pd.read_csv(new_file)
    # hitting or pitching?
    file_cols = file_df.columns
    hit_upload = file_df[~file_df['HitID'].isin(rapsodo_hitting['HitID'])]
    hit_upload = hit_upload.to_dict(orient="records")

    # file_df.replace("-", np.nan, inplace=True)
    file_df['Date'] = pd.to_datetime(file_df['Date']).dt.strftime('%Y-%m-%d')
    
    # upload button
    upload = st.button("Upload Rapsodo Data")
    if upload:
        if "Pitch ID" in file_cols:
            pitch_upload = file_df[~file_df['Pitch ID'].isin(rapsodo_pitching['Pitch ID'])]
            pitch_upload = pitch_upload.to_dict(orient="records")
            response = supabase.table("rapsodo_pitching").insert(pitch_upload).execute()
                        
            # Mark the form as submitted
            st.session_state.form_submitted = True

            # Display success message
            st.success("Data successfully uploaded")

        else:
            hit_upload = file_df[~file_df['HitID'].isin(rapsodo_hitting['HitID'])]
            hit_upload = hit_upload.to_dict(orient="records")
            response = supabase.table("rapsodo_hitting").insert(hit_upload).execute()
            
            # Mark the form as submitted
            st.session_state.form_submitted = True

            # Display success message
            st.success("Data successfully uploaded")
