import pandas as pd
import streamlit as st
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client

# create connection with supabase

# Use st.secrets to load the URL and key from secrets.toml
supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]

# get secrets from toml
supabase: Client = create_client(supabase_url, supabase_key)

# Create the connection object using SupabaseConnection
db = create_client(supabase_url, supabase_key)

# Function to fetch data from any table
def fetch_table_data(table_name):
    # Execute the SQL query
    df = supabase.table(f"{table_name}").select("*").execute().data
    
    # Convert the fetched data into a pandas DataFrame
    return pd.DataFrame(df)

# Fetch data from all tables, then align id to supabase index
players = fetch_table_data('players')
players.set_index('id',inplace=True)
coaches = fetch_table_data('coaches')
coaches.set_index('id',inplace=True)
notes = fetch_table_data('notes')
notes.set_index('id',inplace=True)

# assign class levels to index of years
classdict = {
        0: "Grad",
        1: "Freshman",
        2: "Sophomore",
        3: "Junior",
        4: "Senior",
        5: "Middle"
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

# Authentication
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

# Assign types of notes
note_types = ['Fielder','Hitter','Pitcher']

# create currentplayers table
currentplayers = players.query('active == True')

# Prepare dropdown options (e.g., "John Doe - ID: 123")
player_options = players['full_name'].to_dict()  # {id: full_name}
coach_options = coaches['name'].to_dict()  # {id: name}

if authenticate():
    #streamlit app
    st.title('Devon Prep Coaches App')
    st.subheader('Track Player Updates Below')
    st.text('Tables below default to active players only')
    ptoggle = st.toggle('Pitchers?')
    if ptoggle:
        fplayers = players.query('pitcher == True & active == True')[['first_name','last_name','class']]
    else:
        fplayers = players[['first_name','last_name','class','pos_1','pos_2','pos_3']].fillna('')
    fplayers

    #player notes

    st.title('Input New Player Note')

    with st.form(key='Input New Player Note'):
        note_pitcher = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id])  # Displays name
        note_date = st.date_input("Today's Date", value=date.today())  # Default value to today's date
        note_coach = st.selectbox("Coach", options=list(coach_options.keys()), format_func=lambda id: coach_options[id])  # Displays name
        note_type = st.selectbox("Type", note_types)  # Dropdown for note types
        note_note = st.text_input("Note")  # Input field for the note text
        note_submit = st.form_submit_button(label="Submit Note")

    # When form is submitted
    if note_submit:
        # Convert the date object to ISO 8601 string format
        note_date_str = note_date.isoformat()  # Converts the date object to 'YYYY-MM-DD'

        # Create new note dictionary with IDs
        new_note = {
            'player_id': note_pitcher,
            'date': note_date_str,  # Use the string version of the date
            'coach_id': note_coach,
            'type': note_type,
            'note': note_note
        }

        # Mark the form as submitted
        st.session_state.form_submitted = True

        # Display success message
        st.success("Note submitted successfully")

        # Display spinner for 3 seconds
        with st.spinner("Processing..."):
            # Use a placeholder to keep the spinner visible for 3 seconds
            time.sleep(3)

        # Clear form fields by setting session state variable to False and rerun
        st.session_state.form_submitted = False
        st.experimental_rerun()