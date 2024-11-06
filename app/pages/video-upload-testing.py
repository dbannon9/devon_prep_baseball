#%% Imports

import pandas as pd
import streamlit as st
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client

#%% create connection with supabase

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

# Fetch data from all tables, then align id to supabase index
players = fetch_table_data('players')
players.set_index('id',inplace=True)
# coaches = fetch_table_data('coaches')
# coaches.set_index('id',inplace=True)
# notes = fetch_table_data('notes')
# notes.set_index('id',inplace=True)
video = fetch_table_data('video')
video.set_index('id',inplace=True)

# Create Players Full Name Column
players['full_name'] = players['first_name'] + ' ' + players['last_name']

# Prepare dropdown options
player_options = players['full_name'].to_dict()
pitch_type_options = {
    "4-Seam Fastball",
    "2-Seam Fastball",
    "Changeup",
    "Splitter",
    "Curveball",
    "Slider",
    "Sweeper"
}

#%% Video Upload and Bucket Connection

vid = st.file_uploader("Place Video Here",['mp4','mov'])
video_submit = None

if vid is not None:
    with st.form(key='Input Key Video Information',clear_on_submit=True):
        video_player = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id])  # Displays name
        video_date = st.date_input("Date", value=date.today())  # Default value to today's date
        video_type = st.selectbox("Video Type", options=list({"Pitcher","Hitter","Fielder"}))
        video_view = st.selectbox("View", options=list({"Pitcher's Mound","Home Plate","Open Side","Closed Side"}))
        video_pitch_type = st.selectbox("Pitch Type", options=list(pitch_type_options))
        video_speed = st.selectbox("Video Speed", options=list({"Slo-Mo","Regular"}))
        if video_date is not None:
            video_date_str = video_date.isoformat()  # Converts the date object to 'YYYY-MM-DD'
        video_file_name = f"{video_player} - {video_pitch_type} - {video_speed} - {video_view} - {video_date_str}"
        video_submit = st.form_submit_button(label="Upload Video")
elif vid is None:
    st.write("Please upload a video")

if video_submit == True:
    # Start by loading the video from the uploader into the pitchers bucket
    response = supabase.storage.from_('pitchers').upload(video_file_name, vid)
    # Then get the URL of the video you just uploaded and save it with the same naming convention as above
    video_url = supabase.storage.from_('pitchers').get_public_url(video_file_name)
    # Then create the new row for the videos table with above info
    new_video_row = {
        'player_id': video_player,
        'date': video_date_str,
        'type': video_type,
        'view': video_view,
        'pitch_type': video_pitch_type,
        'speed': video_speed,
        'url': video_url
    }
    response = supabase.table("video").insert(new_video_row).execute()

    # Mark the form as submitted
    st.session_state.form_submitted = True

    # Display success message
    st.success("Note submitted successfully")






