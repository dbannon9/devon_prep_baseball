import pandas as pd
import streamlit as st
from streamlit_sqlalchemy import StreamlitAlchemyMixin
from datetime import date
import math
from decimal import Decimal
from dotenv import load_dotenv
import os
import psycopg2

# create connection with supabase
load_dotenv()
pw = os.getenv('supabasetoken')
db = psycopg2.connect("postgresql://postgres.xtmfmfkpgommfdujhvev:"+pw+"@aws-0-us-east-1.pooler.supabase.com:6543/postgres")

# create a cursor object to gather all data from database
cur = db.cursor()
# Function to fetch data from any table
def fetch_table_data(table_name):
    # Execute the SQL query
    cur.execute(f"SELECT * FROM {table_name}")
    
    # Fetch all rows from the executed query
    rows = cur.fetchall()

    # Get column names from the cursor description
    columns = [desc[0] for desc in cur.description]

    # Convert the fetched data into a pandas DataFrame
    return pd.DataFrame(rows, columns=columns)

# Fetch data from all tables, then align id to supabase index
players = fetch_table_data('players')
players.set_index('id',inplace=True)
coaches = fetch_table_data('coaches')
coaches.set_index('id',inplace=True)
notes = fetch_table_data('notes')
notes.set_index('id',inplace=True)

# Close the cursor and connection
cur.close()
db.close()

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
    password = st.sidebar.text_input("Password", type='password')

    if password == "p1":
        return True
    elif password:
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
        # Create new note dictionary with IDs
        new_note = {
            'player_id': note_pitcher,
            'date': note_date,
            'coach_id': note_coach,
            'type': note_type,
            'note': note_note
        }

        # Re-open the connection for insertion
        with psycopg2.connect("postgresql://postgres.xtmfmfkpgommfdujhvev:"+pw+"@aws-0-us-east-1.pooler.supabase.com:6543/postgres") as db:
            insert_query = """
            INSERT INTO notes (player_id, date, coach_id, type, note)
            VALUES (%s, %s, %s, %s, %s)
            """
            with db.cursor() as cur:
                cur.execute(insert_query, (note_pitcher, note_date, note_coach, note_type, note_note))
                db.commit()  # Commit the transaction

        # Display success message
        st.success("Note submitted successfully!")