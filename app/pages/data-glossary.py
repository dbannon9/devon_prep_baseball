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
import sys
sys.path.append('..')

#%% Page Configuration

st.set_page_config(page_title="Bandbox - Glossary", page_icon=r"app/images/bandbox.png", layout="wide")

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
glossary = fetch_table_data('glossary')

#%% Page

st.title("Bandbox Glossary")
st.markdown("_Read up on all the data you see throughout the app_")
st.html(
    '''
    <style>
    hr {
        border-color: yellow;
    }
    </style>
    '''
)
#%% Hitting Glossary Display
st.header("Hitting Data", divider="yellow")

# Filter to Hitting only
hitting_glossary = glossary[glossary['type'] == 'Hitting']

# Get ordered levels
hitting_levels = hitting_glossary['level'].dropna().unique()

for level in hitting_levels:
    st.subheader(level, divider="yellow")

    level_df = hitting_glossary[hitting_glossary['level'] == level]

    for _, row in level_df.iterrows():
        expander_label = row['term']

        # Add unit to label if available
        if pd.notna(row.get('unit')):
            expander_label += f" ({row['unit']})"

        with st.expander(expander_label):
            if row.get('sentence_definition'):
                st.markdown(f"**Definition:** {row['sentence_definition']}")

            if row.get('paragraph_definition'):
                st.markdown(row['paragraph_definition'])

#%% Pitching Glossary Display
st.header("Pitching Data", divider="yellow")

# Filter to Pitching only
pitching_glossary = glossary[glossary['type'] == 'Pitching']

# Get ordered levels
pitching_levels = pitching_glossary['level'].dropna().unique()

for level in pitching_levels:
    st.subheader(level, divider="yellow")

    level_df = pitching_glossary[pitching_glossary['level'] == level]

    for _, row in level_df.iterrows():
        expander_label = row['term']

        # Add unit to label if available
        if pd.notna(row.get('unit')):
            expander_label += f" ({row['unit']})"

        with st.expander(expander_label):
            if row.get('sentence_definition'):
                st.markdown(f"**Definition:** {row['sentence_definition']}")

            if row.get('paragraph_definition'):
                st.markdown(row['paragraph_definition'])
