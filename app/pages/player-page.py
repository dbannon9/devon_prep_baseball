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
from matplotlib.ticker import MultipleLocator
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



#%% Prepare DK Stats

# merge players onto DK data and filter dates
swings['created_date'] = pd.to_datetime(swings['created_date'], errors='coerce')
dkhit = swings.merge(players_reset,left_on='player_id', right_on='id', how='left')
player_dkhit = dkhit[dkhit['player_id']==player_select]
player_dkhit = player_dkhit[
    (player_dkhit['created_date'] >= pd.to_datetime(start_date)) & 
    (player_dkhit['created_date'] <= pd.to_datetime(end_date))
]

# prep percentile data
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


#%% Prepare Rapsodo Hitting Stats

# merge player_id onto rapsodo data
raphit = rapsodo_hitting.merge(players_reset,left_on='Player ID', right_on='rapsodo_id', how='left').rename(columns = {'id':'player_id'})
player_raphit = raphit[raphit['player_id']==player_select][raphit['ExitVelocity']!="-"]
player_raphit['Date'] = pd.to_datetime(player_raphit['Date'], errors='coerce')
player_raphit = player_raphit[
    (player_raphit['Date'] >= pd.to_datetime(start_date)) & 
    (player_raphit['Date'] <= pd.to_datetime(end_date))
]


#%% Prepare Rapsodo Pitching Stats

# merge player_id onto rapsodo data
rappitch = rapsodo_pitching.merge(
    players_reset,left_on='Player ID', right_on='rapsodo_id', how='left'
    ).rename(columns = {'id':'player_id'})

pitch_type_replace_dict = {
    "Fastball": "Four Seam",
    "Other": "Other",
    "-": "-",
    "Splitter": "Splitter",
    "Slider": "Slider",
    "Cutter": "Cutter",
    "ChangeUp": "Changeup",
    "CurveBall": "Curveball",
    "TwoSeamFastball": "Two Seam"
}

rappitch["Pitch Type"] = rappitch["Pitch Type"].replace(pitch_type_replace_dict)

player_rappitch = rappitch[rappitch['player_id']==player_select]
player_rappitch['Date'] = pd.to_datetime(player_rappitch['Date'], errors='coerce')
player_rappitch = player_rappitch[
    (player_rappitch['Date'] >= pd.to_datetime(start_date)) & 
    (player_rappitch['Date'] <= pd.to_datetime(end_date))
]

# clean up data
player_rappitch_clean = player_rappitch[
    player_rappitch['Pitch Type'].notna() & (player_rappitch['Pitch Type'] != "-") & (player_rappitch['Pitch Type'] != "Other")
]

# List of columns to convert to numeric
numeric_cols = [
    'HB (trajectory)',
    'VB (trajectory)',
    'Velocity',
    'Total Spin',
    'Spin Efficiency (release)',
    'Release Angle',
    'Release Height',
    'Release Side'
]

# Convert all columns to numeric
for col in numeric_cols:
    player_rappitch_clean[col] = pd.to_numeric(player_rappitch_clean[col], errors='coerce')

# Group by Pitch Type: calculate mean and count
pitch_types_player_rappitch = (
    player_rappitch_clean
    .groupby('Pitch Type')[numeric_cols]
    .mean()
    .reset_index()
)

# Calculate counts per pitch type
pitch_counts = (
    player_rappitch_clean
    .groupby('Pitch Type')
    .size()
    .reset_index(name='#')
)

# Merge counts into your means dataframe
pitch_types_player_rappitch = pitch_types_player_rappitch.merge(pitch_counts, on='Pitch Type')
pitch_types_player_rappitch = pitch_types_player_rappitch.sort_values(by='#', ascending=False)


#%% Display Pitching Stats

if players_reset[players_reset['id']==player_select].iloc[0]['pitcher'] == True:
    st.header("Pitching Data",divider = "yellow")
    if len(player_rappitch) < 1:
        st.write("No Rapsodo Pitching Stats Available")
    else:
        plot, table = st.columns(2,gap="large")
        with plot:
            st.subheader("Pitch Shapes by Pitch Type", divider="yellow")

            # Plot
            fig, ax = plt.subplots(figsize=(8, 8))
            fig.patch.set_facecolor("#000e29")
            ax.set_facecolor("#000e29")

            # Scatter plot
            ax.scatter(
                pitch_types_player_rappitch['HB (trajectory)'],
                pitch_types_player_rappitch['VB (trajectory)'],
                color="#f1d71c",
                edgecolor="white",
                s=80
            )

            # Add labels for each point
            for i, row in pitch_types_player_rappitch.iterrows():
                ax.text(
                    row['HB (trajectory)'],
                    row['VB (trajectory)'],
                    row['Pitch Type'],
                    fontsize=11,        # slightly bigger labels
                    ha='right',
                    color='white',
                    fontweight='medium'
                )

            # Axes limits
            ax.set_xlim(-25, 25)
            ax.set_ylim(-25, 25)

            # Axes lines
            ax.axhline(0, color="#f1d71c", linewidth=0.8)
            ax.axvline(0, color="#f1d71c", linewidth=0.8)

            # Title and labels
            # ax.set_title('Average Pitch Shapes by Pitch Type', color='white', fontsize=18, fontweight='bold')
            ax.set_xlabel('Horizontal Break (in)', color='white', fontsize=14, labelpad=10)
            ax.set_ylabel('Vertical Break (in)', color='white', fontsize=14, labelpad=10)

            # Grid and ticks
            ax.grid(True, color='lightgray', linestyle='--', linewidth=0.5)
            ax.tick_params(colors='white', labelsize=12)
            
            # Set spine colors to white
            for spine in ax.spines.values():
                spine.set_color('white')

            # Display
            st.pyplot(fig)

        with table:
            pitch_types_player_rappitch.rename(columns = {
                "Spin Efficiency (release)": "Spin Efficiency",
                "HB (trajectory)": "H Break",
                "VB (trajectory)": "V Break"
            }, inplace=True)
            st.subheader("Pitch Stats", divider = "yellow")
            st.dataframe(pitch_types_player_rappitch,
                         hide_index = True,
                         column_order=("Pitch Type",
                                       "#",
                                       "Velocity",
                                       "Total Spin",
                                       "Spin Efficiency",
                                       "H Break",
                                       "V Break"),
                         column_config={
                            "#": st.column_config.NumberColumn("#", format="%.0f"),
                            "H Break": st.column_config.NumberColumn("H Break", format="%.1f"),
                            "V Break": st.column_config.NumberColumn("V Break", format="%.1f"),
                            "Velocity": st.column_config.NumberColumn("Velocity", format="%.1f"),
                            "Total Spin": st.column_config.NumberColumn("Total Spin", format="%.0f"),
                            "Spin Efficiency": st.column_config.NumberColumn("Spin Efficiency", format="%.2f%%"),
                            }
                         )

            st.subheader("Release Data by Pitch Type", divider = "yellow")    
            # Create figure
            fig_release, ax_release = plt.subplots(figsize=(8, 3))
            fig_release.patch.set_facecolor("#000e29")
            ax_release.set_facecolor("#000e29")

            # Scatter plot: X = Release Side, Y = Release Height
            ax_release.scatter(
                pitch_types_player_rappitch['Release Side'],
                pitch_types_player_rappitch['Release Height'],
                color="#f1d71c",
                edgecolor="white",
                s=80
            )

            # Add labels for each point (Pitch Type)
            for i, row in pitch_types_player_rappitch.iterrows():
                ax_release.text(
                    row['Release Side'],
                    row['Release Height'],
                    row['Pitch Type'],
                    fontsize=11,
                    ha='right',
                    color='white',
                    fontweight='medium'
                )

            # Axes limits
            ax_release.set_xlim(-3, 3)
            ax_release.set_ylim(3, 7)
            # ax_release.set_aspect('equal', adjustable='box')

            # Horizontal gridlines at whole numbers
            ax_release.yaxis.set_major_locator(MultipleLocator(1))

            # Axes lines through origin
            ax_release.axhline(5, color="#f1d71c", linewidth=0.8)
            ax_release.axvline(0, color="#f1d71c", linewidth=0.8)

            # Title and Labels
            # ax_release.set_title('Average Release by Pitch Type', color='white', fontsize=18, fontweight='bold')
            ax_release.set_xlabel('Release Side (ft)', color='white', fontsize=14, labelpad=10)
            ax_release.set_ylabel('Release Height (ft)', color='white', fontsize=14, labelpad=10)

            # Grid and ticks
            ax_release.grid(True, color='lightgray', linestyle='--', linewidth=0.5)
            ax_release.tick_params(colors='white', labelsize=12)

            # Set spine colors to white
            for spine in ax_release.spines.values():
                spine.set_color('white')


            # Display in Streamlit
            st.pyplot(fig_release)

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

st.header("Hitting Data",divider = "yellow")

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