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
coaches = fetch_table_data('coaches')
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
swings = fetch_table_data('swings')

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

#%% Leaderboard Page

st.header("Player Tables")

classes_and_dates_column, inactive_column = st.columns(2)

with classes_and_dates_column:
    classes_select = st.multiselect("Select Classes", options=active_classes, default=active_classes)
    dates_select = st.date_input("Select Dates",
                                 value=[datetime.today()-relativedelta(months=1),
                                        datetime.today()],
                                 max_value=datetime.today()
                                 )

with inactive_column:
    inactive_toggle = st.toggle("Show Inactive Players?", value=False)

#%% Rapsodo Leaderboards

## Hitting

# filter players by above filters

# Default for inactive_toggle
if 'inactive_toggle' not in locals():
    inactive_toggle = False

# Filter by active status
if not inactive_toggle:
    filtered_players = players_show.query("active == True")
else:
    filtered_players = players_show.copy()  # show all

# Further filter by selected classes
if classes_select:
    filtered_players = filtered_players[filtered_players['class'].isin(classes_select)]

# filter data by dates selected
rapsodo_hitting['Date'] = pd.to_datetime(rapsodo_hitting['Date'], errors='coerce')

filtered_rapsodo_hitting = rapsodo_hitting[
    (rapsodo_hitting['Date'] >= pd.to_datetime(dates_select[0])) & 
    (rapsodo_hitting['Date'] <= pd.to_datetime(dates_select[1]))
]

# merge for id purposes
raphit = filtered_rapsodo_hitting.merge(filtered_players,left_on='Player ID', right_on='rapsodo_id', how='left')
raphit['ExitVelocity'] = pd.to_numeric(raphit['ExitVelocity'], errors='coerce')[raphit['ExitVelocity']!="-"]

# group by id
raphit_group = raphit.groupby('rapsodo_id').agg(
    ExitVelocity_max=('ExitVelocity', 'max'),
    ExitVelocity_avg=('ExitVelocity', 'mean'),
    ExitVelocity_90th_percentile=('ExitVelocity', lambda x: np.percentile(x, 90))
).reset_index()

# join full_name back on
raphit_group = raphit_group.merge(
    players_show[['rapsodo_id', 'full_name']], 
    on='rapsodo_id', 
    how='left'
)

# col rename
raphit_group.rename(columns={
    'full_name': 'Player',
    'ExitVelocity_max': 'Max EV',
    'ExitVelocity_avg': 'Average EV',
    'ExitVelocity_90th_percentile': '90th pct EV',
}, inplace=True)

# sort
raphit_group.sort_values(by='Average EV', ascending=False, inplace=True)

# Define custom colormap (deep navy replacing white)
colors = ["blue", "black", "red"]  # Adjust as needed
custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom_coolwarm", colors)

# Function to apply color gradient
def highlight_ev(df):
    return df.style.background_gradient(
        cmap=custom_cmap,  # Use the custom colormap
        subset=['Max EV', 'Average EV', '90th pct EV']
    ).format({'Max EV': '{:.1f}', 'Average EV': '{:.1f}', '90th pct EV': '{:.1f}'})

# Display leaderboard
st.subheader("Rapsodo Leaderboard")
if len(raphit_group) == 0:
    st.write("No Data Available for Selected Dates and Classes")
else:
    st.dataframe(
        highlight_ev(raphit_group[['Player', 'Average EV', '90th pct EV', 'Max EV']]),
        hide_index=True,
    )

