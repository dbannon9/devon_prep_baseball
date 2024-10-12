#%% Imports

import pandas as pd
import streamlit as st
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client

#%% Connect to Supabase

# Use st.secrets to load the URL and key from secrets.toml
supabase_url = st.secrets["supabase"]["SUPABASE_URL"]
supabase_key = st.secrets["supabase"]["SUPABASE_KEY"]

# get secrets from toml
supabase: Client = create_client(supabase_url, supabase_key)

# Create the connection object using SupabaseConnection
db = create_client(supabase_url, supabase_key)

#%% Data Retrieval

# Function to fetch data from any table
def fetch_table_data(table_name):
    # Execute the SQL query
    df = supabase.table(f"{table_name}").select("*").execute().data
    
    # Convert the fetched data into a pandas DataFrame
    return pd.DataFrame(df)

# Fetch data from all tables, then align id to supabase index
practice_plans = fetch_table_data('practice_plans')
practice_plans.set_index('id',inplace=True)

#%% View Practice Plans
st.title("View Practice Plans")
pdate = st.date_input("Select Practice Date", value=date.today())
pdate = pdate.strftime('%Y-%m-%d')

this_practice = practice_plans[practice_plans['date']==pdate]

if this_practice.empty:
    st.write("No practice plan found for this date.")

else:
    # Extract the event name for the row
    # event_1_name = this_practice.iloc[0]['event_1_name']
    st.subheader(f"{str(this_practice.iloc[0]['event_1_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_1_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_1_name']}")
    st.write(f"{this_practice.iloc[0]['event_1_notes']}")
    if this_practice.iloc[0]['event_2_name'] == "":
        print("")
    else:
        st.subheader(f"{str(this_practice.iloc[0]['event_2_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_2_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_2_name']}")
        st.write(f"{this_practice.iloc[0]['event_2_notes']}")
        if this_practice.iloc[0]['event_3_name'] == "":
            print("")
        else:
            st.subheader(f"{str(this_practice.iloc[0]['event_3_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_3_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_3_name']}")
            st.write(f"{this_practice.iloc[0]['event_3_notes']}")
            if this_practice.iloc[0]['event_4_name'] == "":
                print("")
            else:
                st.subheader(f"{str(this_practice.iloc[0]['event_4_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_4_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_4_name']}")
                st.write(f"{this_practice.iloc[0]['event_4_notes']}")
