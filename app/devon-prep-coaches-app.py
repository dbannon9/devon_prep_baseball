#%% Imports

import pandas as pd
import streamlit as st
import sys, shutil, pathlib
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

# cache resets
for p in pathlib.Path(".").rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)

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
users = fetch_table_data('users')

#%% Run the App
st.set_page_config(layout="wide")

st.logo(r'app/images/dp_logo_transparent.png', size='large')

@st.dialog("Welcome to The Devon Prep Baseball App. Log In to Continue.",width = "Large",dismissible=False)
def login_dialog():
    if st.button("Sign in with Google"):
        st.login(provider="google")

if not st.user.is_logged_in:
    login_dialog()

with st.sidebar:
    if st.user.is_logged_in:
        st.write(f"Logged in as **{st.user.name}**")

        if st.button("Log out"):
            st.logout()

if st.user.is_logged_in:
    current_user_email = st.user.email
    current_user_type = users.loc[users['email'] == current_user_email, 'type'].iloc[0]
    if not users['email'].isin([st.user.email]).any():
        st.write("You do not have access to this app. Please contact your coach.")
    elif current_user_type == "Player":
        #%% page definitions
        player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
        nav = st.navigation([
            player_page,
        ])
    else:
        roster = st.Page("pages/roster-page.py",title="Home",icon=":material/tsunami:")
        team_leaderboards = st.Page("pages/team-leaderboards.py",title="Leaderboards",icon=":material/social_leaderboard:")
        player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
        plate_discipline_tracking = st.Page("pages/plate-discipline-tracking.py",title="Plate Discipline Tracking",icon=":material/background_dot_small:")
        data_input = st.Page("pages/data-input.py",title="Data Upload",icon=":material/upload:")
        nav = st.navigation([
            roster,
            team_leaderboards,
            player_page,
            data_input,
            plate_discipline_tracking
        ])
        nav.run()