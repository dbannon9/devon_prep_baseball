#%% Imports

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, time
import math
from decimal import Decimal
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from st_supabase_connection import SupabaseConnection

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

#%% Player Page

st.title('Player Summary Page')

player_select = st.selectbox("Player", options=list(player_options.keys()), format_func=lambda id: player_options[id])

players_reset = players_show.reset_index()

#%% Prepare DK Stats

# merge players onto DK data
dkhit = swings.merge(players_reset,left_on='player_id', right_on='id', how='left')
player_dkhit = dkhit[dkhit['player_id']==player_select]
player_class = players_reset[players_reset['id']==player_select]['class'].iloc[0]
dk_curves_class = dk_curves[dk_curves['class'] == player_class]

def get_percentile(value, curve_row):
    percentiles = [1,10,20,30,40,50,60,70,80,90,99]
    values = [curve_row[f"p_{p}"] for p in percentiles]

    # linear interpolation
    if value <= values[0]:
        return percentiles[0]
    if value >= values[-1]:
        return percentiles[-1]
    
    for i in range(1, len(values)):
        if value < values[i]:
            # interpolate between two percentile points
            lower_p, upper_p = percentiles[i-1], percentiles[i]
            lower_v, upper_v = values[i-1], values[i]
            interp = lower_p + (value - lower_v) * (upper_p - lower_p) / (upper_v - lower_v)
            return round(interp, 1)
    return None


#%% Prepare Rapsodo Stats

# merge player_id onto rapsodo data
raphit = rapsodo_hitting.merge(players_reset,left_on='Player ID', right_on='rapsodo_id', how='left').rename(columns = {'id':'player_id'})
player_raphit = raphit[raphit['player_id']==player_select][raphit['ExitVelocity']!="-"]

#%% Display Hitting Stats

# Define custom colormap (blue → black → red)
colors = ["blue", "black", "red"]
custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom_percentile", colors)

# Apply gradient only to the Percentile column
def highlight_percentile(df):
    return df.style.background_gradient(
        cmap=custom_cmap,
        subset=['Percentile by Class'],
        vmin=0,
        vmax=100
    ).format({'Percentile by Class': '{:.1f}'})


diamond_kinetics, rapsodo = st.columns(2,gap="large")

with diamond_kinetics:
    st.subheader("Diamond Kinetics Data",divider = "yellow")

    # Generate rapsodo data
    if len(player_dkhit) < 1:
        st.write('No Diamond Kinetic Hitting Stats Available')
    else:
        hand_speed_avg = round(pd.to_numeric(player_dkhit['max_hand_speed'], errors='coerce').mean(), 1)
        barrel_speed_avg = round(pd.to_numeric(player_dkhit['max_barrel_speed'], errors='coerce').mean(), 1)
        attack_angle_avg = round(pd.to_numeric(player_dkhit['attack_angle'], errors='coerce').mean(), 1)
        hand_speed_std = round(pd.to_numeric(player_dkhit['max_hand_speed'], errors='coerce').std(), 1)
        barrel_speed_std = round(pd.to_numeric(player_dkhit['max_barrel_speed'], errors='coerce').std(), 1)
        attack_angle_std = round(pd.to_numeric(player_dkhit['attack_angle'], errors='coerce').std(), 1)
        hs_curve = dk_curves_class[dk_curves_class['metric'] == 'hand_speed'].iloc[0]
        bs_curve = dk_curves_class[dk_curves_class['metric'] == 'barrel_speed'].iloc[0]
        aa_curve = dk_curves_class[dk_curves_class['metric'] == 'attack_angle'].iloc[0]
        hand_speed_pct = get_percentile(hand_speed_avg, hs_curve)
        barrel_speed_pct = get_percentile(barrel_speed_avg, bs_curve)
        attack_angle_pct = get_percentile(attack_angle_avg, aa_curve)
        dk_df = pd.DataFrame({
            'Metric': ['Hand Speed', 'Barrel Speed', 'Attack Angle'],
            'Average': [hand_speed_avg, barrel_speed_avg, attack_angle_avg],
            'Standard Deviation': [hand_speed_std, barrel_speed_std, attack_angle_std],
            'Percentile by Class': [hand_speed_pct, barrel_speed_pct, attack_angle_pct]
        })
        dk_df = dk_df.round(1)
        st.dataframe(highlight_percentile(dk_df),
                     hide_index=True,
                     column_config={
                         'Average':st.column_config.NumberColumn("Average", format="%.1f"),
                         'Standard Deviation':st.column_config.NumberColumn("Standard Deviation", format="%.1f"),
                         'Percentile by Class':st.column_config.NumberColumn("Percentile by Class", format="%.1f")
                     })

with rapsodo:
    st.subheader("Rapsodo Data",divider = "yellow")
    
    # Generate rapsodo data
    if len(player_raphit) < 1:
        st.write('No Rapsodo Hitting Stats Available')
    else:
        ev_max = max(pd.to_numeric(player_raphit['ExitVelocity'], errors='coerce'))
        ev_avg = round(pd.to_numeric(player_raphit['ExitVelocity'], errors='coerce').mean(), 1)
        ev_90 = round(np.percentile(pd.to_numeric(player_raphit['ExitVelocity'], errors='coerce').dropna(), 90), 1)
        rap_df = pd.DataFrame({
            'Metric': ['Max EV', '90th pct EV', 'Average EV'],
            'Value': [ev_max, ev_90, ev_avg]
        })
        
        st.dataframe(rap_df, hide_index=True)