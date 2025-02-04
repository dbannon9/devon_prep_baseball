import pandas as pd
import streamlit as st
from datetime import date, time, timedelta
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

# Fetch data from all tables, then align id to supabase index
players = fetch_table_data('players')
players.set_index('id',inplace=True)
notes = fetch_table_data('notes')
notes.set_index('id',inplace=True)
throw_session = fetch_table_data('throw_session')
throw_session.set_index('id',inplace=True)

#%% Data Adjustments

# assign class levels to index of years
classdict = {
        0: "Middle",
        1: "Senior",
        2: "Junior",
        3: "Sophomore",
        4: "Freshman",
        5: "Grad"
}

# assign class year names to each player based on graduation year
def classdef(thing):
    class_years = []
    for thing in players['grad_year']:
        if isinstance(thing, Decimal):
            thing = int(thing)
        years_diff = math.ceil((date(thing, 9, 1) - date.today()).days / 365)
        if years_diff >= 5:
            return 5
        elif years_diff <1:
            return 0
        class_year = classdict.get(years_diff)
        class_years.append(class_year)
    players['class'] = class_years
classdef(players['grad_year'])

# Create Players Full Name Column
players['full_name'] = players['first_name'] + ' ' + players['last_name']

# assign player active status by class
active_classes = ['Freshman','Sophomore','Junior','Senior']
players['active'] = players['class'].isin(active_classes)

# create currentplayers table
currentplayers = players.query('active == True')

# create currentpitchers table
currentpitchers = players.query('pitcher == True')

# Prepare dropdown options
current_pitcher_options = currentpitchers['full_name'].to_dict()
session_types = ['Bullpen','Sim Game','Scrimmage','Game']

# Add player names to sessions
player_dict = players['full_name'].to_dict()
throw_session['player_name'] = throw_session['player_id'].map(player_dict)

# Create display version of throw table
show_throw_session = throw_session[['date','player_name','type','num_pitches','warmups_included','note']]
show_throw_session.rename(columns={
                          'date': 'Date',
                          'player_name': 'Player',
                          'type': 'Type',
                          'num_pitches': 'Pitches',
                          'warmups_included': 'Warmups Included?',
                          'note': 'Note'
                          }, inplace=True)

# Assign days
today = date.today()
d1 = (today - timedelta(days=1)).isoformat()
d2 = (today - timedelta(days=2)).isoformat()
d3 = (today - timedelta(days=3)).isoformat()
d4 = (today - timedelta(days=4)).isoformat()

# Create daily session list
sessions_today = show_throw_session.query(f"Date == '{today}'")
sessions_d1 = show_throw_session.query(f"Date == '{d1}'")
sessions_d2 = show_throw_session.query(f"Date == '{d2}'")
sessions_d3 = show_throw_session.query(f"Date == '{d3}'")
sessions_d4 = show_throw_session.query(f"Date == '{d4}'")

#%% Arm Tracking

st.title('Recent Sessions')

if len(sessions_today) == 0:
    st.subheader(f'No sessions today')
else:
    st.subheader(f'Today''s Sessions')
    st.dataframe(sessions_d1,hide_index=True)

if len(sessions_d1) == 0:
    st.subheader(f'No sessions from {d1}')
else:
    st.subheader(f'Sessions from {d1}')
    st.dataframe(sessions_d1,hide_index=True)

if len(sessions_d2) == 0:
    st.subheader(f'No sessions from {d2}')
else:
    st.subheader(f'Sessions from {d2}')
    st.dataframe(sessions_d2,hide_index=True)

if len(sessions_d3) == 0:
    st.subheader(f'No sessions from {d3}')
else:
    st.subheader(f'Sessions from {d3}')
    st.dataframe(sessions_d3,hide_index=True)

if len(sessions_d4) == 0:
    st.subheader(f'No sessions from {d4}')
else:
    st.subheader(f'Sessions from {d4}')
    st.dataframe(sessions_d4,hide_index=True)

#%% Input Sesstion

st.title('Input New Session')

with st.form(key='Input New Player session',clear_on_submit=True):
    session_pitcher = st.selectbox("Player", options=list(current_pitcher_options.keys()), format_func=lambda id: current_pitcher_options[id])  # Displays name
    session_date = st.date_input("Date", value=date.today())  # Default value to today's date
    session_type = st.selectbox("Type", session_types)  # Dropdown for session types
    session_warmups_included = st.checkbox("Warmups Included?")
    session_num_pitches = st.number_input("Number of Pitches",1,100)
    session_note = st.text_input("Note")  # Input field for the note text
    session_submit = st.form_submit_button(label="Submit Session")

# When form is submitted
if session_submit:
    # Convert the date object to ISO 8601 string format
    session_date_str = session_date.isoformat()  # Converts the date object to 'YYYY-MM-DD'

    # Create new note dictionary with IDs
    new_session = {
        'player_id': session_pitcher,
        'date': session_date_str,  # Use the string version of the date
        'warmups_included': session_warmups_included,
        'num_pitches': session_num_pitches,
        'type': session_type,
        'note': session_note
    }

    # Push using insert function
    response = supabase.table("throw_session").insert(new_session).execute()

    # Mark the form as submitted
    st.session_state.form_submitted = True

    # Display success message
    st.success("Session submitted successfully")

