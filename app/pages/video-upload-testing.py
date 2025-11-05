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
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Ellipse
from dateutil.relativedelta import relativedelta

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
coaches = fetch_table_data('coaches')
video = fetch_table_data('video')

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

# Prepare dropdown options
player_options = players['full_name'].to_dict()
pitch_type_options = {
    "Four Seam",
    "Two Seam",
    "Cutter"
    "Changeup",
    "Splitter",
    "Curveball",
    "Slider",
}

#%% Video Upload and Bucket Connection

vid = st.file_uploader("Place Video Here", type=['mp4', 'mov'])
video_submit = None

if vid is not None:
    with st.form(key='Input Key Video Information',clear_on_submit=True):
        video_player = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id])  # Displays name
        video_date = st.date_input("Date", value=date.today())  # Default value to today's date
        video_type = st.selectbox("Video Type", options=list({"Pitcher","Hitter","Fielder"}))
        video_speed = st.selectbox("Video Speed", options=list({"Slo-Mo","Regular"}))
        video_view = st.selectbox("View", options=list({"Pitcher's Mound","Home Plate","Open Side","Closed Side"}))
        if video_type == 'Pitcher':
            video_pitch_type = st.selectbox("Pitch Type", options=list(pitch_type_options)) 
        if video_date is not None:
            video_date_str = video_date.isoformat()  # Converts the date object to 'YYYY-MM-DD'
        if video_type == "Pitcher":
            video_file_name = f"{video_player} - {video_type} - {video_pitch_type} - {video_speed} - {video_view} - {video_date_str}.mov"
        else:
            video_file_name = f"{video_player} - {video_type} - {video_speed} - {video_view} - {video_date_str}.mov"
        video_submit = st.form_submit_button(label="Upload Video")
elif vid is None:
    st.write("Please upload a video")

# Check if the user uploaded a video
if video_submit:
    try:
        # Upload the video file to the Supabase storage bucket
        response = db.storage.from_('pitching').upload(video_file_name, vid, file_options={"contentType": "video/quicktime"})

        # Get the public URL of the uploaded video
        video_url = db.storage.from_('pitching').get_public_url(video_file_name)

        # Insert the video details into the database
        new_video_row = {
            'player_id': video_player,
            'date': video_date_str,
            'type': video_type,
            'view': video_view,
            'pitch_type': video_pitch_type,
            'speed': video_speed,
            'url': video_url
        }
        insert_response = db.table("video").insert(new_video_row).execute()

        st.success("Video uploaded successfully and saved in the database.")

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")