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
users = fetch_table_data('users')
rapsodo_hitting = fetch_table_data('rapsodo_hitting')
rapsodo_pitching = fetch_table_data('rapsodo_pitching')
swings = fetch_table_data('swings')
goals = fetch_table_data('goals')

# Assign user variables from users table

current_user_email = st.user.email
current_user_type = users.loc[users['email'] == current_user_email, 'type'].iloc[0]

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

#%% Home Page
 
st.title("Player Goals")

#%% Player Select

active_players = players_show[players_show['active'] == True]

player_options = dict(zip(active_players.index, active_players['full_name']))

if current_user_type == "Player":
    player_select = users.loc[users['email'] == current_user_email, 'player_id'].iloc[0]
    st.markdown(f"Showing player data for ***{players.loc[players['id'] == player_select, 'full_name'].iloc[0]}***")
else:
    player_select = st.selectbox(
        "Player",
        options=list(player_options.keys()),
        format_func=lambda id: player_options[id]
    )

# get ordered goals for player

goals_sorted = goals[goals['player_id'] == player_select].sort_values(by=["created_at"],ascending=False)

# Loop through each unique timeframe
for timeframe in goals_sorted["timeframe"].unique():

    # Filter dataframe for that timeframe
    df_timeframe = goals_sorted[goals_sorted["timeframe"] == timeframe]
    goal_num = 1
    with st.expander(f"{timeframe}"):
        goal_len = len(df_timeframe)
        for _, row in df_timeframe.iterrows():
            st.subheader(f"Goal #{goal_num}")
            st.markdown(
                f"""
                <b>Statistic:</b> {row['statistic']}<br>
                <b>Baseline:</b> {row['baseline']}<br>
                <b>Target:</b> {row['target']}
                <hr>
                """,
                unsafe_allow_html=True
            )
            if goal_len > goal_num:
                st.divider()
                goal_num = goal_num + 1
            else:
                goal_num = goal_num + 1        


# # # # # # #%% Input New Players

# # # # # # st.subheader("Input New Players", divider="yellow")
# # # # # # default_year = datetime.now().year + 4
# # # # # # positions = [None, "C", "1B", "2B", "3B", "SS", "OF", "UT"]

# # # # # # with st.form("input_new_players", clear_on_submit=True, enter_to_submit=False, border=True):
# # # # # #     first_name = st.text_input("First Name")
# # # # # #     last_name = st.text_input("Last Name")
# # # # # #     grad_year = st.number_input("HS Graduation Year", value=default_year)
# # # # # #     email = st.text_input("Email")
# # # # # #     pitcher = st.checkbox("Pitcher?", value=False)
# # # # # #     pos_1 = st.selectbox("Primary Position", positions)
# # # # # #     pos_2 = st.selectbox("Secondary Position", positions)
# # # # # #     pos_3 = st.selectbox("Tertiary Position", positions)
# # # # # #     rapsodo_id = st.text_input("Rapsodo ID")
# # # # # #     player_submit = st.form_submit_button(label="Submit")

# # # # # # def clean_value(value):
# # # # # #     if value in ("", None):
# # # # # #         return None
# # # # # #     return value

# # # # # # if player_submit:
# # # # # #     new_player = {
# # # # # #         "first_name": clean_value(first_name),
# # # # # #         "last_name": clean_value(last_name),
# # # # # #         "grad_year": clean_value(grad_year),
# # # # # #         "pitcher": clean_value(pitcher),
# # # # # #         "pos_1": clean_value(pos_1),
# # # # # #         "pos_2": clean_value(pos_2),
# # # # # #         "pos_3": clean_value(pos_3),
# # # # # #         "rapsodo_id": clean_value(rapsodo_id),
# # # # # #     }
# # # # # #     response = db.client.table("players").insert(new_player).execute()
# # # # # #     new_player_id = response.data[0]["id"]
# # # # # #     new_user = {
# # # # # #         "email": clean_value(email),
# # # # # #         "type": "Player",
# # # # # #         "player_id": clean_value(new_player_id)
# # # # # #     }
# # # # # #     response2 = db.client.table("users")
# # # # # #     st.session_state.form_submitted = True
# # # # # #     st.success("New Player Added")
