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
from matplotlib.patches import Ellipse
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

#%% Player Page

st.title('Player Summary Page')

# ✅ Only include active players
active_players = players_show[players_show['active'] == True]

player_options = dict(zip(active_players.index, active_players['full_name']))

player_select = st.selectbox(
    "Player",
    options=list(player_options.keys()),
    format_func=lambda id: player_options[id]
)

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

if len(player_dkhit) > 0:
    # Define individual statistics and create dk_df for player page
    hand_speed_avg = round(pd.to_numeric(player_dkhit['max_hand_speed'], errors='coerce').mean(), 1)
    barrel_speed_avg = round(pd.to_numeric(player_dkhit['max_barrel_speed'], errors='coerce').mean(), 1)
    impact_momentum_avg = round(pd.to_numeric(player_dkhit['impact_momentum'], errors='coerce').mean(), 1)
    attack_angle_avg = round(pd.to_numeric(player_dkhit['attack_angle'], errors='coerce').mean(), 1)
    hand_speed_std = round(pd.to_numeric(player_dkhit['max_hand_speed'], errors='coerce').std(), 1)
    barrel_speed_std = round(pd.to_numeric(player_dkhit['max_barrel_speed'], errors='coerce').std(), 1)
    impact_momentum_std = round(pd.to_numeric(player_dkhit['impact_momentum'], errors='coerce').std(), 1)
    attack_angle_std = round(pd.to_numeric(player_dkhit['attack_angle'], errors='coerce').std(), 1)
    hs_curve = dk_curves_class[dk_curves_class['metric'] == 'hand_speed'].iloc[0]
    bs_curve = dk_curves_class[dk_curves_class['metric'] == 'barrel_speed'].iloc[0]
    im_curve = dk_curves_class[dk_curves_class['metric'] == 'impact_momentum'].iloc[0]
    aa_curve = dk_curves_class[dk_curves_class['metric'] == 'attack_angle'].iloc[0]
    hand_speed_pct = get_percentile(hand_speed_avg, hs_curve)
    barrel_speed_pct = get_percentile(barrel_speed_avg, bs_curve)
    impact_momentum_pct = get_percentile(impact_momentum_avg, im_curve)
    attack_angle_pct = get_percentile(attack_angle_avg, aa_curve)
    dk_df = pd.DataFrame({
        'Metric': ['Hand Speed', 'Barrel Speed', 'Impact', 'Attack Angle'],
        'Average': [hand_speed_avg, barrel_speed_avg, impact_momentum_avg, attack_angle_avg],
        'Standard Deviation': [hand_speed_std, barrel_speed_std, impact_momentum_std, attack_angle_std],
        'Percentile by Class': [hand_speed_pct, barrel_speed_pct, impact_momentum_pct, attack_angle_pct]
    })

    # Create date-grouped dataset

    hit_numeric_cols = [
        'max_hand_speed',
        'max_barrel_speed',
        'impact_momentum',
        'attack_angle'
    ]

    for col in hit_numeric_cols:
        player_dkhit[col] = pd.to_numeric(player_dkhit[col], errors='coerce')

    player_date_dk_stats = (
        player_dkhit
        .groupby('created_date')[hit_numeric_cols]
        .agg(['mean', 'std'])
        .reset_index()
    )

    # Flatten column names
    player_date_dk_stats.columns = ['_'.join(col).rstrip('_') for col in player_date_dk_stats.columns.values]


    curve_lookup = {
        'max_hand_speed': dk_curves_class[dk_curves_class['metric'] == 'hand_speed'].iloc[0],
        'max_barrel_speed': dk_curves_class[dk_curves_class['metric'] == 'barrel_speed'].iloc[0],
        'impact_momentum': dk_curves_class[dk_curves_class['metric'] == 'impact_momentum'].iloc[0],
        'attack_angle': dk_curves_class[dk_curves_class['metric'] == 'attack_angle'].iloc[0]
    }

    for metric in hit_numeric_cols:
        mean_col = f"{metric}_mean"
        pct_col = f"{metric}_pct"

        player_date_dk_stats[pct_col] = player_date_dk_stats[mean_col].apply(
            lambda val: get_percentile(val, curve_lookup[metric]) if pd.notna(val) else None
        )

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

# color map by pitch type
pitch_colors = {
    "Four Seam": "#c63316",
    "Other": "#ffffff",
    "-": "#ffffff",
    "Splitter": "#fa7100",
    "Slider": "#984893",
    "Cutter": "#4d30ff",
    "Changeup": "#f3ae00",
    "Curveball": "#46a576",
    "Two Seam": "#4f8fff"
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

# Group by Pitch Type: calculate mean and std
pitch_types_stats = (
    player_rappitch_clean
    .groupby('Pitch Type')[numeric_cols]
    .agg(['mean', 'std'])
    .reset_index()
)

# Flatten multi-index columns
pitch_types_stats.columns = ['_'.join(col).rstrip('_') for col in pitch_types_stats.columns.values]

# Merge counts
pitch_counts = (
    player_rappitch_clean
    .groupby('Pitch Type')
    .size()
    .reset_index(name='#')
)

pitch_types_player_rappitch = pitch_types_stats.merge(pitch_counts, left_on='Pitch Type', right_on='Pitch Type')
pitch_types_player_rappitch = pitch_types_player_rappitch.sort_values(by='#', ascending=False)
pitch_types_player_rappitch["color"] = pitch_types_player_rappitch["Pitch Type"].map(pitch_colors)

### Timeline Data

pitch_types_by_date_stats = (
    player_rappitch_clean
    .groupby(['Date', 'Pitch Type'])[numeric_cols]
    .agg(['mean', 'std'])
    .reset_index()
)

# Flatten multi-index columns
pitch_types_by_date_stats.columns = ['_'.join(col).rstrip('_') for col in pitch_types_by_date_stats.columns.values]

# Merge pitch counts by Date + Pitch Type
pitch_counts_by_date = (
    player_rappitch_clean
    .groupby(['Date', 'Pitch Type'])
    .size()
    .reset_index(name='#')
)

# add pitch counts on
pitch_types_by_date = pitch_types_by_date_stats.merge(
    pitch_counts_by_date,
    left_on=['Date', 'Pitch Type'],
    right_on=['Date', 'Pitch Type']
)

# Sort by velo and add colors
pitch_types_by_date = pitch_types_by_date.sort_values(['Date', 'Velocity_mean'], ascending=[True, False])
pitch_types_by_date["color"] = pitch_types_by_date["Pitch Type"].map(pitch_colors)


#%% Create Hitting and Pitching Tabs

hitting, pitching = st.tabs(["Hitting", "Pitching"])

    #%% Display Hitting Stats

with hitting:
    st.header("Hitting Data",divider = "yellow")
    if len(player_dkhit) == 0 and len(player_raphit) == 0:
        st.write('No Hitting Data Available')
    else:
        hitting_charts, hitting_timelines = st.tabs(["Charts & Data","Timelines"])
        #%% Hitting Charts
        with hitting_charts:
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

                # Generate dk data
                if len(player_dkhit) < 1:
                    st.write('No Diamond Kinetic Hitting Stats Available')
                else:
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
        #%% Timelines
        with hitting_timelines:
            st.subheader("Diamond Kinetics Metric by Date",divider = "yellow")
            if len(player_dkhit) == 0:
                st.write('No Diamond Kinetic Hitting Stats Available')
            else:
                metric_map = {
                    "Hand Speed": ("max_hand_speed_mean", "max_hand_speed_std", "max_hand_speed_pct"),
                    "Barrel Speed": ("max_barrel_speed_mean", "max_barrel_speed_std", "max_barrel_speed_pct"),
                    "Impact Momentum": ("impact_momentum_mean", "impact_momentum_std", "impact_momentum_pct"),
                    "Attack Angle": ("attack_angle_mean", "attack_angle_std", "attack_angle_pct")
                }
                
                metric_select = st.selectbox(
                    "Select Metric",
                    options=list(metric_map.keys()),
                    index=0
                )

                mean_col, std_col, pct_col = metric_map[metric_select]

                fig, ax1 = plt.subplots(figsize=(10, 4))
                fig.patch.set_facecolor("#000e29")
                ax1.set_facecolor("#000e29")

                # Primary axis: mean + std
                ax1.plot(
                    player_date_dk_stats["created_date"], 
                    player_date_dk_stats[mean_col],
                    marker="o",
                    linewidth=2,
                    label=f"{metric_select} Mean",
                    color="#f1d71c"
                )

                # error bars
                ax1.errorbar(
                    player_date_dk_stats["created_date"],
                    player_date_dk_stats[mean_col],
                    yerr=player_date_dk_stats[std_col],
                    fmt="o-",
                    linewidth=2,
                    capsize=4,
                    color="#f1d71c",
                    label=f"{metric_select} Mean ±1 STD",
                )
                # Set y limits and labels
                curve_row = dk_curves_class[
                    dk_curves_class['metric'] == metric_select.lower().replace(" ", "_")
                ].iloc[0]
                y_min = curve_row["p_1"]
                y_max = curve_row["p_99"]
                ax1.set_ylim(y_min, y_max)
                ax1.set_ylabel(f"{metric_select}", color="white", fontsize=14)
                ax1.tick_params(axis="y", colors="white")

                # Secondary axis: percentile % scale
                ax2 = ax1.twinx()
                ax2.plot(
                    player_date_dk_stats["created_date"], 
                    player_date_dk_stats[pct_col],
                    marker="s",
                    linestyle="--",
                    linewidth=1.5,
                    label=f"{metric_select} Percentile",
                    color="white"
                )

                ax2.set_ylim(0, 100)
                ax2.set_ylabel("Percentile (%)", color="white", fontsize=14)
                ax2.tick_params(axis="y", colors="white")

                # X axis
                ax1.set_xlabel("Date", color="white", fontsize=14)
                ax1.tick_params(axis="x", colors="white", rotation=45)

                # Grid & styling
                ax1.grid(True, linestyle="--", alpha=0.3)

                for spine in ax1.spines.values():
                    spine.set_color("white")
                for spine in ax2.spines.values():
                    spine.set_color("white")

                # Dark legend
                lines_1, labels_1 = ax1.get_legend_handles_labels()
                lines_2, labels_2 = ax2.get_legend_handles_labels()
                ax1.legend(
                    lines_1 + lines_2,
                    labels_1 + labels_2,
                    facecolor="#000e29", 
                    edgecolor="white",
                    labelcolor="white"
                )

                st.pyplot(fig)


    #%% Display Pitching Stats

with pitching:

    st.header("Pitching Data",divider = "yellow")
    if len(player_rappitch) < 1:
        st.write("No Rapsodo Pitching Stats Available")
    else:
        charts, timelines = st.tabs(["Charts & Data","Timelines"])
        #%% Charts and pitch type data
        with charts:
            plot, table = st.columns(2,gap="large")
            with plot:
                st.subheader("Pitch Shapes by Type", divider="yellow")

                # Plot
                fig, ax = plt.subplots(figsize=(8, 8))
                fig.patch.set_facecolor("#000e29")
                ax.set_facecolor("#000e29")

                # Scatter plot
                ax.scatter(
                    pitch_types_player_rappitch['HB (trajectory)_mean'],
                    pitch_types_player_rappitch['VB (trajectory)_mean'],
                    color=pitch_types_player_rappitch['color'],
                    edgecolor="white",
                    s=80
                )

                # Add ellipses for each pitch type
                for i, row in pitch_types_player_rappitch.iterrows():
                    hb_std = row['HB (trajectory)_std']
                    vb_std = row['VB (trajectory)_std']
                    
                    ellipse = Ellipse(
                        (row['HB (trajectory)_mean'], row['VB (trajectory)_mean']),
                        width=2*hb_std,   # 2*std for ±1σ
                        height=2*vb_std,
                        edgecolor=row['color'],
                        facecolor='none',
                        linestyle='--',
                        linewidth=1.5
                    )
                    ax.add_patch(ellipse)

                # Add labels for each point
                for i, row in pitch_types_player_rappitch.iterrows():
                    ax.text(
                        row['HB (trajectory)_mean'],
                        row['VB (trajectory)_mean'],
                        row['Pitch Type'],
                        fontsize=11,
                        ha='right',
                        color='white',
                        fontweight='medium'
                    )

                # Axes limits
                ax.set_xlim(-30, 30)
                ax.set_ylim(-30, 30)

                # Axes lines
                ax.axhline(0, color="#f1d71c", linewidth=0.8)
                ax.axvline(0, color="#f1d71c", linewidth=0.8)

                # Labels
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
                    "Spin Efficiency (release)_mean": "Spin Efficiency",
                    "HB (trajectory)_mean": "H Break",
                    "VB (trajectory)_mean": "V Break",
                    "Velocity_mean": "Velocity",
                    "Total Spin_mean": "Spin Rate"
                }, inplace=True)

                # Function to apply color styling
                def color_pitch_type(val):
                    color = pitch_colors.get(val, "#000000")  # fallback color if missing
                    text_color = "black" if val in ["Other", "-"] else "white"
                    return f"background-color: {color}; color: {text_color}; font-weight: bold;"

                # Apply styling to the dataframe
                # Apply styling to the dataframe
                style_df = (
                    pitch_types_player_rappitch.style
                    .applymap(color_pitch_type, subset=["Pitch Type"])  # keep your original coloring
                    .set_table_styles([
                        {'selector': 'th', 'props': [('color', 'white'), ('font-weight', 'bold')]}  # header text
                    ])
                )

                st.subheader("Pitch Stats", divider = "yellow")
                st.dataframe(style_df,
                            hide_index = True,
                            column_order=("Pitch Type",
                                        "#",
                                        "Velocity",
                                        "Spin Rate",
                                        "Spin Efficiency",
                                        "H Break",
                                        "V Break"),
                            column_config={
                                "#": st.column_config.NumberColumn("#", format="%.0f"),
                                "H Break": st.column_config.NumberColumn("H Break", format="%.1f"),
                                "V Break": st.column_config.NumberColumn("V Break", format="%.1f"),
                                "Velocity": st.column_config.NumberColumn("Velocity", format="%.1f"),
                                "Spin Rate": st.column_config.NumberColumn("Spin Rate", format="%.0f"),
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
                    pitch_types_player_rappitch['Release Side_mean'],
                    pitch_types_player_rappitch['Release Height_mean'],
                    color=pitch_types_player_rappitch['color'],
                    edgecolor="white",
                    s=80
                )

                # Axes limits
                ax_release.set_xlim(-3, 3)
                ax_release.set_ylim(3, 7)
                # ax_release.set_aspect('equal', adjustable='box')

                # Horizontal gridlines at whole numbers
                ax_release.yaxis.set_major_locator(MultipleLocator(1))

                # Axis line yellow
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
        #%% Timelines
        with timelines:
            st.subheader("Pitch Velocity by Date",divider = "yellow")
            # Filter pitch types to only those available in dataset
            available_pitch_types = sorted(pitch_types_by_date['Pitch Type'].unique())

            pitch_filter = st.multiselect(
                "Select Pitch Types",
                options=available_pitch_types,
                default=available_pitch_types
            )

            # Filter dataset to selected pitch types
            filtered_data = pitch_types_by_date[
                pitch_types_by_date['Pitch Type'].isin(pitch_filter)
            ]

            # Create figure
            fig_vel, ax_vel = plt.subplots(figsize=(10, 4))
            fig_vel.patch.set_facecolor("#000e29")
            ax_vel.set_facecolor("#000e29")

            # Plot per pitch type with colors & ± std error bars
            for pitch in pitch_filter:
                subset = filtered_data[filtered_data['Pitch Type'] == pitch]

                ax_vel.errorbar(
                    subset['Date'],
                    subset['Velocity_mean'],
                    yerr=subset['Velocity_std'],    # 1 standard deviation
                    fmt='o-',                       # circle markers + line
                    markersize=6,
                    linewidth=2,
                    label=pitch,
                    color=subset['color'].iloc[0],  # use mapped color
                    ecolor=subset['color'].iloc[0], # error bar color
                    capsize=4,
                    elinewidth=1.5,
                    zorder=3
                )

            # Axes formatting
            ax_vel.set_xlim(filtered_data['Date'].min(), filtered_data['Date'].max())
            ax_vel.set_ylim(60, 95)

            ax_vel.set_xlabel("Date", color='white', fontsize=14)
            ax_vel.set_ylabel("Velocity (mph)", color='white', fontsize=14)

            # Grid & ticks
            ax_vel.grid(True, linestyle='--', alpha=0.3)
            ax_vel.tick_params(colors='white')

            # Spine styling
            for spine in ax_vel.spines.values():
                spine.set_color('white')

            # Legend styling
            ax_vel.legend(facecolor="#000e29", edgecolor="white", labelcolor="white")

            # Display in Streamlit
            st.pyplot(fig_vel)

