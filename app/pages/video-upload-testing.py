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

if vid is None:
    st.write("Please upload a video")
else:
    video_player = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id], index=None)
    video_date = st.date_input("Date", value=date.today())
    video_type = st.selectbox("Video Type", ["Pitcher", "Hitter", "Fielder"], index=None)
    video_speed = st.selectbox("Video Speed", ["Slo-Mo", "Regular"], index=None)
    video_view = st.selectbox("View", ["Pitcher's Mound","Home Plate","Open Side","Closed Side"], index=None)
    video_pitch_type = None
    if video_type == "Pitcher":
        video_pitch_type = st.selectbox("Pitch Type", list(pitch_type_options), index=None)

    video_submit = st.button("Upload Video")

# Check if the user uploaded a video
if video_submit and vid is not None:

    # Convert date
    video_date_str = video_date.isoformat()

    # Base filename
    if video_type == "Pitcher":
        base_name = f"{video_player} - {video_type} - {video_pitch_type} - {video_speed} - {video_view} - {video_date_str}"
    else:
        base_name = f"{video_player} - {video_type} - {video_speed} - {video_view} - {video_date_str}"

    # ---- STEP 1: Generate a unique filename ----
    ext = ".mov"
    file_name = base_name + ext

    bucket = "pitching" if video_type == "Pitcher" else "hitting"

    # Get list of existing files in the bucket
    existing_files = db.client.storage.from_(bucket).list()

    existing_names = [f["name"] for f in existing_files]

    counter = 1
    while file_name in existing_names:
        file_name = f"{base_name}-{counter}{ext}"
        counter += 1

    # ---- STEP 2: Upload ----
    file_bytes = vid.read()

    response = db.client.storage.from_(bucket).upload(
        file_name,
        file_bytes,
        file_options={"contentType": "video/quicktime"}
    )

    video_url = db.client.storage.from_(bucket).get_public_url(file_name)

    # ---- STEP 3: Insert database row ----
    new_video_row = {
        'player_id': video_player,
        'date': video_date_str,
        'type': video_type,
        'view': video_view,
        'speed': video_speed,
        'url': video_url
    }

    if video_type == "Pitcher":
        new_video_row['pitch_type'] = video_pitch_type

    db.client.table("video").insert(new_video_row).execute()

    st.success(f"Uploaded: {file_name}")