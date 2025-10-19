#%% Imports

import pandas as pd
import streamlit as st
import sys, shutil, pathlib

# cache resets
for p in pathlib.Path(".").rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)


#%% page definitions

roster = st.Page("pages/roster-page.py",title="Home",icon=":material/tsunami:")
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

if authenticate():
    nav = st.navigation([
        roster,
      # note_input,
        player_page,
      # team_notes_page,
      # arm_tracking_page,
      # calendar_page,
      # view_practice_plans_page,
      # practice_planning_page2,
      # practice_planning_page,
        data_input
      # video_upload_testing
        ])
    nav.run()