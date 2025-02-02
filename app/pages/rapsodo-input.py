#%% Imports

import pandas as pd
import streamlit as st
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

#%% .csv Data Dump

st.title("Rapsodo Data Input")
new_file = st.file_uploader("Dump Rapsodo 'pitchinggroup' File Here",type='csv')
if new_file:
    upload = st.button("Upload Rapsodo Pitching Data")
    file_df = pd.read_csv(new_file)
    if upload:
        response = supabase.table("rapsodo_pitching").insert(file_df).execute()
        
        # Mark the form as submitted
        st.session_state.form_submitted = True

        # Display success message
        st.success("Note submitted successfully")
