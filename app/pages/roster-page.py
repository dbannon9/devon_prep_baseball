#%% Imports

import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import numpy as np
from datetime import date, time
import math
from decimal import Decimal
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

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
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
swings = fetch_table_data('swings')

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
coach_options = coaches['name'].to_dict()

#%% Home Page
 
st.title("Devon Prep Baseball")

#%% Roster Toggles

st.subheader("Roster & Positions", divider = "yellow")
edit_toggle = st.toggle('Edit?')
ptoggle = st.toggle('Pitchers?')
if ptoggle:
    fplayers = players_show.query('pitcher == True & active == True')[['first_name','last_name','class']]
    fplayers.rename(columns={
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'class': 'Grade Level'
        }, inplace=True)
else:
    fplayers = players_show[['first_name','last_name','class','pos_1','pos_2','pos_3']].fillna('')
    fplayers.rename(columns={
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'class': 'Grade Level',
        'pos_1': 'Primary Position',
        'pos_2': 'Secondary Position',
        'pos_3': 'Tertiary Position'
    }, inplace=True)

if edit_toggle:
    players_update = st.data_editor(players)
    save = st.button("Save")
    if save:
        for idx, row in players_update.iterrows():
            player_id = row.name  # This accesses the index (which is 'id' in your case)
            response = db.table("players").update(row.to_dict()).eq('id', player_id).execute()
    
        # Mark the form as submitted
        st.session_state.form_submitted = True

        # Display success message
        st.success("Data successfully saved")


else:
    st.dataframe(fplayers,hide_index=True)
