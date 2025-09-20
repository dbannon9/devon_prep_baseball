#%% Imports

import pandas as pd
import streamlit as st
import numpy as np
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client


# inspect immediate directory & repo root (best-effort)
parent = pathlib.Path(__file__).parent
st.write("Directory listing of the page's folder:", sorted(os.listdir(parent)))
# attempt to locate other files with similar names / suspicious tokens in the repo
root = pathlib.Path(__file__).parents[2] if len(pathlib.Path(__file__).parents) >= 3 else pathlib.Path(".")
st.write("Guessed repo root:", str(root))

hits = []
for p in root.rglob("*.py"):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    # look for the exact problem tokens that would cause your KeyError
    if "players_show['class']" in txt or "assign_class(" in txt or "grad_year" in txt:
        hits.append(str(p))
# limit output
st.write("Files in repo containing players_show/class/assign_class/grad_year (first 200):")
st.write(hits[:200])

# quick sanity: print the names of the first 20 files under repo root
try:
    sample_files = [str(x.relative_to(root)) for x in sorted(root.rglob("*"))[:200]]
    st.write("Sample repo files (first 200):", sample_files)
except Exception:
    pass

st.write("sys.path (first entries):", sys.path[:6])
st.write("End diagnostics.")



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

    # file_df.replace("-", np.nan, inplace=True)
    file_df['Date'] = pd.to_datetime(file_df['Date']).dt.strftime('%Y-%m-%d')
    
    # upload button
    upload = st.button("Upload Rapsodo Data")
    if upload:
        if "Pitch ID" in file_cols:
            pitch_upload = file_df[~file_df['Pitch ID'].isin(rapsodo_pitching['Pitch ID'])]
            if len(pitch_upload) == 0:
                st.success("Pitching Data is Up To Date")
            else:
                pitch_upload = pitch_upload.to_dict(orient="records")
                response = supabase.table("rapsodo_pitching").insert(pitch_upload).execute()
                # Mark the form as submitted
                st.session_state.form_submitted = True
                # Display success message
                st.success("Data Successfully Uploaded")

        else:
            hit_upload = file_df[~file_df['HitID'].isin(rapsodo_hitting['HitID'])]
            if len(hit_upload) == 0:
                st.success("Hitting Data is Up To Date")
            else:
                hit_upload = hit_upload.to_dict(orient="records")
                st.json(hit_upload)
                response = supabase.table("rapsodo_hitting").insert(hit_upload).execute()
                # Mark the form as submitted
                st.session_state.form_submitted = True
                # Display success message
                st.success("Data Successfully Uploaded")
