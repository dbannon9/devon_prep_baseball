#%% Imports

import pandas as pd
import streamlit as st
import sys, shutil, pathlib

# cache resets
for p in pathlib.Path(".").rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)

#%% page definitions

roster = st.Page("pages/roster-page.py",title="Home",icon=":material/tsunami:")
team_leaderboards = st.Page("pages/team-leaderboards.py",title="Leaderboards",icon=":material/social_leaderboard:")
player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
data_input = st.Page("pages/data-input.py",title="Data Upload",icon=":material/upload:")

#%% Authentication

def authenticate():
    st.sidebar.header('Login')
    entered_password = st.sidebar.text_input("Password", type='password')
    
    # Access the password from secrets
    correct_password = st.secrets["authentication"]["password"]

    if entered_password == correct_password:
        return True
    elif entered_password:
        st.sidebar.error("Incorrect password")
    return False

#%% Run the App
st.set_page_config(layout="wide")

# st.logo(r'app/images/dp_logo_transparent.png', size='large')

if authenticate():
    nav = st.navigation([
        roster,
        team_leaderboards,
        player_page,
        data_input
        ])
    nav.run()