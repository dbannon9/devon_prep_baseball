#%% Imports

import pandas as pd
import streamlit as st
from datetime import date, time
import math
from decimal import Decimal
import os
from supabase import create_client, Client
from fpdf import FPDF
import base64

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
this_practice = practice_plans[practice_plans['date'] == pdate]

# Check if this_practice is empty
if this_practice.empty:
    st.write("No practice plan found for this date.")
    st.stop()
else:
    # Assign practice text names
    print_1 = f"{str(this_practice.iloc[0]['event_1_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_1_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_1_name']}" if this_practice.iloc[0]['event_1_name'] != "" else ""
    print_2 = f"{str(this_practice.iloc[0]['event_2_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_2_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_2_name']}" if this_practice.iloc[0]['event_2_name'] != "" else ""
    print_3 = f"{str(this_practice.iloc[0]['event_3_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_3_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_3_name']}" if this_practice.iloc[0]['event_3_name'] != "" else ""
    print_4 = f"{str(this_practice.iloc[0]['event_4_start_time'])[:5].lstrip('0')} - {str(this_practice.iloc[0]['event_4_end_time'])[:5].lstrip('0')} - {this_practice.iloc[0]['event_4_name']}" if this_practice.iloc[0]['event_4_name'] != "" else ""

    print_note_1 = f"{this_practice.iloc[0]['event_1_notes']}"
    print_note_2 = f"{this_practice.iloc[0]['event_2_notes']}"
    print_note_3 = f"{this_practice.iloc[0]['event_3_notes']}"
    print_note_4 = f"{this_practice.iloc[0]['event_4_notes']}"

    # Add in PDF button
    def create_download_link(val, filename):
        b64 = base64.b64encode(val)  # val looks like b'...'
        return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'

    export_as_pdf = st.button("Export Practice Plans")

    if export_as_pdf:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 24)
        pdf.cell(40, 10, f"Practice Plans: {pdate}", ln=2)
        pdf.set_font('Helvetica', 'I', 16)
        pdf.cell(40, 10, f"{str(print_1)}", ln=2)
        pdf.set_font('Helvetica', '', 12)
        pdf.cell(40, 10, f"{str(print_note_1)}", ln=2)
        if this_practice.iloc[0]['event_2_name'] != '':
            pdf.set_font('Helvetica', 'I', 16)
            pdf.cell(40, 10, f"{str(print_2)}", ln=2)
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(40, 10, f"{str(print_note_2)}", ln=2)
        if this_practice.iloc[0]['event_3_name'] != '':
            pdf.set_font('Helvetica', 'I', 16)
            pdf.cell(40, 10, f"{str(print_3)}", ln=2)
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(40, 10, f"{str(print_note_3)}", ln=2)
        if this_practice.iloc[0]['event_4_name'] != '':
            pdf.set_font('Helvetica', 'I', 16)
            pdf.cell(40, 10, f"{str(print_4)}", ln=2)
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(40, 10, f"{str(print_note_4)}", ln=2)
        html = create_download_link(pdf.output(dest="S").encode("latin-1"), "test")
        st.markdown(html, unsafe_allow_html=True)

    # Extract the event name for the row
    st.divider()
    st.write(this_practice.iloc[0]['coach_quote'])
    st.divider()
    st.subheader(print_1)
    st.write(print_note_1)
    if this_practice.iloc[0]['event_2_name'] != "":
        st.subheader(print_2)
        st.write(print_note_2)
    if this_practice.iloc[0]['event_3_name'] != "":
        st.subheader(print_3)
        st.write(print_note_3)
    if this_practice.iloc[0]['event_4_name'] != "":
        st.subheader(print_4)
        st.write(print_note_4)
