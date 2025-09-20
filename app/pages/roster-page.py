#%% Imports

import streamlit as st
# import pandas as pd
# import numpy as np
# from datetime import date, time
# import math
# from decimal import Decimal
# import os
# from supabase import create_client, Client
# import matplotlib.pyplot as plt
# import matplotlib.colors as mcolors

# diagnostics - paste at TOP of pages/roster-page.py
import os, sys, pathlib
import streamlit as st

st.markdown("### ROSTER-PAGE.RAW DIAGNOSTICS")

st.write("__file__ (executed file):", __file__)
st.write("cwd:", os.getcwd())

# show the file content that the server is executing (first chunk)
try:
    file_path = pathlib.Path(__file__)
    content = file_path.read_text(errors="ignore")
    st.write("First 2000 chars of this file (as read by server):")
    st.code(content[:2000])
except Exception as e:
    st.write("Could not read __file__ content:", e)

# inspect immediate directory & repo root (best-effort)
parent = pathlib.Path(__file__).parent
st.write("Directory listing of the page's folder:", sorted(os.listdir(parent)))
# attempt to locate other files with similar names / suspicious tokens in the repo
root = pathlib.Path(__file__).parents[2] if len(pathlib.Path(__file__).parents) >= 3 else pathlib.Path(".")
st.write("Guessed repo root:", str(root))

hits = []
for p in root.rglob("*.py"):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    # look for the exact problem tokens that would cause your KeyError
    if "players_show['class']" in txt or "assign_class(" in txt or "grad_year" in txt:
        hits.append(str(p))
# limit output
st.write("Files in repo containing players_show/class/assign_class/grad_year (first 200):")
st.write(hits[:200])

# quick sanity: print the names of the first 20 files under repo root
try:
    sample_files = [str(x.relative_to(root)) for x in sorted(root.rglob("*"))[:200]]
    st.write("Sample repo files (first 200):", sample_files)
except Exception:
    pass

st.write("sys.path (first entries):", sys.path[:6])
st.write("End diagnostics.")



# #%% Connect to Supabase

# # Use st.secrets to load the URL and key from secrets.toml
# supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
# supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]

# # get secrets from toml
# supabase: Client = create_client(supabase_url, supabase_key)

# # Create the connection object using SupabaseConnection
# db = create_client(supabase_url, supabase_key)

# #%% Data Retrieval

# # Function to fetch data from any table
# def fetch_table_data(table_name):
#     # Execute the SQL query
#     df = supabase.table(f"{table_name}").select("*").execute().data
    
#     # Convert the fetched data into a pandas DataFrame
#     return pd.DataFrame(df)

# # Fetch data from all tables, then align id to supabase index
# players = fetch_table_data('players')
# players.set_index('id',inplace=True)
# coaches = fetch_table_data('coaches')
# coaches.set_index('id',inplace=True)
# notes = fetch_table_data('notes')
# notes.set_index('id',inplace=True)
# rapsodo_hitting = fetch_table_data('rapsodo_hitting')
# rapsodo_hitting.set_index('id',inplace=True)
# rapsodo_pitching = fetch_table_data('rapsodo_pitching')
# rapsodo_pitching.set_index('id',inplace=True)

#%% DIAGNOSTIC

st.write("earth to streamlit")
# st.write(players.head())



# #%% Data Adjustments

# # assign class levels to index of years
# classdict = {
#         0: "Middle",
#         1: "Senior",
#         2: "Junior",
#         3: "Sophomore",
#         4: "Freshman",
#         5: "Grad"
# }

# #create the display version of players
# players_show = pd.DataFrame(players.copy())

# # assign class year names to each player based on graduation year
# def assign_class(players_show):
#     class_years = []
#     for gy in players_show['grad_year']:
#         if isinstance(gy, Decimal):
#             gy = int(gy)
#         years_diff = math.ceil((date(gy, 9, 1) - date.today()).days / 365)

#         if years_diff >= 5:
#             class_year = classdict.get(5)
#         elif years_diff < 1:
#             class_year = classdict.get(0)
#         else:
#             class_year = classdict.get(years_diff)

#         class_years.append(class_year)

#     players_show['class'] = class_years
#     return players_show

# if 'grad_year' not in players_show.columns:
#     st.error("No grad_year column found in players_show")
# else:
#     players_show = assign_class(players_show)

# # Create Players Full Name Column
# players_show['full_name'] = players_show['first_name'] + ' ' + players_show['last_name']

# # assign player active status by class
# active_classes = ['Freshman','Sophomore','Junior','Senior']
# players_show['active'] = players_show['class'].isin(active_classes)

# # Assign types of notes
# note_types = ['Fielder','Hitter','Pitcher']

# # create currentplayers table
# currentplayers = players_show.query('active == True')

# # Prepare dropdown options
# player_options = players_show['full_name'].to_dict()
# coach_options = coaches['name'].to_dict()

# #%% Home Page
 
# st.title("Devon Prep Baseball")

# #%% Creating Rapsodo Leaderboards

# ## Hitting

# # merge for id purposes
# raphit = rapsodo_hitting.merge(players_show,left_on='Player ID', right_on='rapsodo_id', how='left')
# raphit['ExitVelocity'] = pd.to_numeric(raphit['ExitVelocity'], errors='coerce')[raphit['ExitVelocity']!="-"]

# # group by id
# raphit_group = raphit.groupby('rapsodo_id').agg(
#     ExitVelocity_max=('ExitVelocity', 'max'),
#     ExitVelocity_avg=('ExitVelocity', 'mean'),
#     ExitVelocity_90th_percentile=('ExitVelocity', lambda x: np.percentile(x, 90))
# ).reset_index()

# # join full_name back on
# raphit_group = raphit_group.merge(
#     players_show[['rapsodo_id', 'full_name']], 
#     on='rapsodo_id', 
#     how='left'
# )

# # col rename
# raphit_group.rename(columns={
#     'full_name': 'Player',
#     'ExitVelocity_max': 'Max EV',
#     'ExitVelocity_avg': 'Average EV',
#     'ExitVelocity_90th_percentile': '90th pct EV',
# }, inplace=True)

# # sort
# raphit_group.sort_values(by='Average EV', ascending=False, inplace=True)

# # # color gradient
# # def highlight_ev(df):
# #     return df.style.background_gradient(
# #         cmap='coolwarm',
# #         subset=['Max EV', 'Average EV', '90th pct EV']
# #     ).format({'Max EV': '{:.1f}', 'Average EV': '{:.1f}', '90th pct EV': '{:.1f}'})

# # # display
# # st.subheader("Rapsodo Leaderboard")
# # st.dataframe(
# #     highlight_ev(raphit_group[['Player', 'Average EV', '90th pct EV', 'Max EV']]),
# #     hide_index=True,
# # )


# # Define custom colormap (deep navy replacing white)
# colors = ["blue", "black", "red"]  # Adjust as needed
# custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom_coolwarm", colors)

# # Function to apply color gradient
# def highlight_ev(df):
#     return df.style.background_gradient(
#         cmap=custom_cmap,  # Use the custom colormap
#         subset=['Max EV', 'Average EV', '90th pct EV']
#     ).format({'Max EV': '{:.1f}', 'Average EV': '{:.1f}', '90th pct EV': '{:.1f}'})

# # Display leaderboard
# st.subheader("Rapsodo Leaderboard")
# st.dataframe(
#     highlight_ev(raphit_group[['Player', 'Average EV', '90th pct EV', 'Max EV']]),
#     hide_index=True,
# )


# #%% Roster Toggles

# st.subheader("Roster & Positions")
# edit_toggle = st.toggle('Edit?')
# ptoggle = st.toggle('Pitchers?')
# if ptoggle:
#     fplayers = players_show.query('pitcher == True & active == True')[['first_name','last_name','class']]
#     fplayers.rename(columns={
#         'first_name': 'First Name',
#         'last_name': 'Last Name',
#         'class': 'Grade Level'
#         }, inplace=True)
# else:
#     fplayers = players_show[['first_name','last_name','class','pos_1','pos_2','pos_3']].fillna('')
#     fplayers.rename(columns={
#         'first_name': 'First Name',
#         'last_name': 'Last Name',
#         'class': 'Grade Level',
#         'pos_1': 'Primary Position',
#         'pos_2': 'Secondary Position',
#         'pos_3': 'Tertiary Position'
#     }, inplace=True)

# if edit_toggle:
#     players_update = st.data_editor(players)
#     save = st.button("Save")
#     if save:
#         for idx, row in players_update.iterrows():
#             player_id = row.name  # This accesses the index (which is 'id' in your case)
#             response = supabase.table("players").update(row.to_dict()).eq('id', player_id).execute()
    
#         # Mark the form as submitted
#         st.session_state.form_submitted = True

#         # Display success message
#         st.success("Data successfully saved")


# else:
#     st.dataframe(fplayers,hide_index=True)
