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
dk_curves = fetch_table_data('dk_curves')

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

#%% Leaderboard Page

st.title("Team Leaderboards")

classes_and_dates_column, inactive_column = st.columns(2)

with classes_and_dates_column:
    classes_select = st.multiselect("Select Classes", options=active_classes, default=active_classes)
    dates_select = st.date_input("Select Dates",
                                 value=[datetime.today()-relativedelta(months=6),
                                        datetime.today()],
                                 max_value=datetime.today()+relativedelta(days=1)
                                 )
    if len(dates_select)<2:
        start_date = pd.to_datetime(dates_select[0])
        end_date = datetime.today()
    else:
        start_date = pd.to_datetime(dates_select[0])
        end_date = pd.to_datetime(dates_select[1])



with inactive_column:
    inactive_toggle = st.toggle("Show Inactive Players?", value=False)

# Configure player tables based on above

players_reset = players_show.reset_index()

# Default for inactive_toggle
if 'inactive_toggle' not in locals():
    inactive_toggle = False

# Filter by active status
if not inactive_toggle:
    filtered_players = players_reset.query("active == True")
else:
    filtered_players = players_reset.copy()  # show all

# Further filter by selected classes
if classes_select:
    filtered_players = filtered_players[filtered_players['class'].isin(classes_select)]

#%% Prepare DK Data


# filter data by dates selected
swings['created_date'] = pd.to_datetime(swings['created_date'], errors='coerce')
filtered_swings = swings[
    (swings['created_date'] >= pd.to_datetime(start_date)) & 
    (swings['created_date'] <= pd.to_datetime(end_date)) &
    (swings['player_id'].isin(filtered_players['id']))
]

# merge for id purposes
dkhit = filtered_swings.merge(filtered_players,left_on='player_id', right_on='id', how='left')

# group by id
dkhit_group = dkhit.groupby('player_id').agg(
    hand_speed_max=('max_hand_speed', 'max'),
    hand_speed_avg=('max_hand_speed', 'mean'),
    hand_speed_90=('max_hand_speed', lambda x: np.percentile(x, 90)),
    hand_speed_std=('max_hand_speed', 'std'),

    barrel_speed_max=('max_barrel_speed', 'max'),
    barrel_speed_avg=('max_barrel_speed', 'mean'),
    barrel_speed_90=('max_barrel_speed', lambda x: np.percentile(x, 90)),
    barrel_speed_std=('max_barrel_speed', 'std'),

    attack_angle_avg=('attack_angle', 'mean'),
    attack_angle_std=('attack_angle', 'std'),

    impact_momentum_avg=('impact_momentum', 'mean'),
    impact_momentum_std=('impact_momentum', 'std'),

    hand_cast_avg=('hand_cast', 'mean'),
    hand_cast_std=('hand_cast', 'std'),

    barrel_x_avg=('barrel_x', 'mean'),
    barrel_x_std=('barrel_x', 'std'),

    barrel_y_avg=('barrel_y', 'mean'),
    barrel_y_std=('barrel_y', 'std'),

    barrel_z_avg=('barrel_z', 'mean'),
    barrel_z_std=('barrel_z', 'std')
).reset_index()

# join full_name back on
dkhit_group = dkhit_group.merge(
    filtered_players[['id', 'full_name', 'class']], 
    left_on='player_id',
    right_on='id',
    how='left'
)

# column rename
dkhit_group.rename(columns={
    'full_name': 'Player',
    'class': 'Class',

    'hand_speed_max': 'Max Hand Speed',
    'hand_speed_avg': 'Avg Hand Speed',
    'hand_speed_90': '90p Hand Speed',
    'hand_speed_std': 'Std Hand Speed',

    'barrel_speed_max': 'Max Barrel Speed',
    'barrel_speed_avg': 'Avg Barrel Speed',
    'barrel_speed_90': '90p Barrel Speed',
    'barrel_speed_std': 'Std Barrel Speed',

    'attack_angle_avg': 'Avg Attack Angle',
    'attack_angle_std': 'Std Attack Angle',

    'impact_momentum_avg': 'Avg Impact',
    'impact_momentum_std': 'Std Impact',

    'hand_cast_avg': 'Avg Hand Cast',
    'hand_cast_std': 'Std Hand Cast',

    'barrel_x_avg': 'Avg Barrel X',
    'barrel_x_std': 'Std Barrel X',

    'barrel_y_avg': 'Avg Barrel Y',
    'barrel_y_std': 'Std Barrel Y',

    'barrel_z_avg': 'Avg Barrel Z',
    'barrel_z_std': 'Std Barrel Z'
}, inplace=True)

dkhit_group.sort_values(by='Avg Barrel Speed', ascending=False, inplace=True)
dkhit_group = dkhit_group.round(2)

#%% Prepare Rapsodo Data

# filter data by dates selected
rapsodo_hitting['Date'] = pd.to_datetime(rapsodo_hitting['Date'], errors='coerce')
filtered_rapsodo_hitting = rapsodo_hitting[
    (rapsodo_hitting['Date'] >= pd.to_datetime(start_date)) & 
    (rapsodo_hitting['Date'] <= pd.to_datetime(end_date))
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
    players_show[['rapsodo_id', 'full_name', 'class']], 
    on='rapsodo_id', 
    how='left'
)

# col rename
raphit_group.rename(columns={
    'full_name': 'Player',
    'class': 'Class',
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

#%% Display leaderboard

# DK first

st.subheader("Diamond Kinetics Leaderboard",divider = "yellow")
if len(dkhit_group) == 0:
    st.write("No Data Available for Selected Dates and Classes")
else:
    st.dataframe(dkhit_group[['Player', 'Class', 'Avg Attack Angle', 'Std Attack Angle', 'Avg Barrel Speed', 'Std Barrel Speed', 'Avg Hand Speed', 'Std Hand Speed']],
                    hide_index=True,
                    column_config={
                        "Avg Attack Angle": st.column_config.NumberColumn("Avg Attack Angle", format="%.2f"),
                        "Std Attack Angle": st.column_config.NumberColumn("Std Attack Angle", format="%.2f"),
                        "Avg Barrel Speed": st.column_config.NumberColumn("Avg Barrel Speed", format="%.2f"),
                        "Std Barrel Speed": st.column_config.NumberColumn("Std Barrel Speed", format="%.2f"),
                        "Avg Hand Speed": st.column_config.NumberColumn("Avg Hand Speed", format="%.2f"),
                        "Std Hand Speed": st.column_config.NumberColumn("Std Hand Speed", format="%.2f"),
                        "Avg Impact": st.column_config.NumberColumn("Avg Impact", format="%.2f"),
                        "Std Impact": st.column_config.NumberColumn("Std Impact", format="%.2f"),
                    },
    )

# Rapsodo

st.subheader("Rapsodo Leaderboard", divider = "yellow")
if len(raphit_group) == 0:
    st.write("No Data Available for Selected Dates and Classes")
else:
    st.dataframe(
        highlight_ev(raphit_group[['Player', 'Class', 'Average EV', '90th pct EV', 'Max EV']]),
        hide_index=True,
    )

#%% show definitions doc

st.subheader("Diamond Kinetics Data Definitions", divider = "yellow")
st.pdf(r'app/documents/dk_definitions.pdf',height=600)

