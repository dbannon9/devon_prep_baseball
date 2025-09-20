#%% Imports

import pandas as pd
import streamlit as st

#%% page definitions

roster = st.Page("pages/roster-page2.py",title="Home",icon=":material/tsunami:")
# note_input = st.Page("pages/note-input-page.py",title="Input Notes",icon=":material/edit_note:")
player_page = st.Page("pages/player-page.py",title="Player Summary",icon=":material/bar_chart:")
# team_notes_page = st.Page("pages/team-notes-page.py",title="Team Notes",icon=":material/group:")
# arm_tracking_page = st.Page("pages/arm-tracking-page.py",title="Arm Tracking",icon=":material/flag:")
# coach_page = st.Page("pages/coaches-page.py",title="Coach Summary",icon=":material/sports:")
# calendar_page = st.Page("pages/calendar-page.py",title="Schedule",icon=":material/calendar_month:")
# view_practice_plans_page = st.Page("pages/view-practice-plans-page.py",title="View Practice Plans",icon=":material/sports:")
# practice_planning_page = st.Page("pages/practice-planning-page.py",title="Practice Planning",icon=":material/conversion_path:")
# practice_planning_page2 = st.Page("pages/practice-planning-page-test2.py",title="TEST - Practice Planning",icon=":material/construction:")
# video_upload_testing = st.Page("pages/video-upload-testing.py",title="Video Upload Testing",icon=":material/upload:")
rapsodo_input = st.Page("pages/rapsodo-input.py",title="Raposodo Upload",icon=":material/upload:")

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
        rapsodo_input
      # video_upload_testing
        ])
    nav.run()