#%% Imports

import pandas as pd
import streamlit as st
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client


#%% page definitions

roster = st.Page("pages/roster-page.py",title="Roster",icon=":material/tsunami:")
note_input = st.Page("pages/note-input-page.py",title="Input Notes",icon=":material/edit_note:")
player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
team_notes_page = st.Page("pages/team-notes-page.py",title="Team Notes",icon=":material/group:")
# coach_page = st.Page("pages/coaches-page.py",title="Coach Summary",icon=":material/sports:")
calendar_page = st.Page("pages/calendar-page.py",title="Schedule",icon=":material/calendar_month:")

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
    nav = st.navigation([roster,note_input,player_page,team_notes_page,calendar_page])
    nav.run()

