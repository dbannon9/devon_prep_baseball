import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from datetime import date
import math
from decimal import Decimal

db = create_engine("postgresql://postgres.xtmfmfkpgommfdujhvev:G#v2!*hq8hU8-aU@aws-0-us-east-1.pooler.supabase.com:6543/postgres").connect()

classdict = {
        0: "grad",
        1: "freshman",
        2: "sophomore",
        3: "junior",
        4: "senior",
        5: "middle"
}

def authenticate():
    st.sidebar.header('Login')
    password = st.sidebar.text_input("Password", type='password')

    if password == "p1":
        return True
    elif password:
        st.sidebar.error("Incorrect password")
    return False

if authenticate():
    players = pd.DataFrame(db.execute(text("SELECT * FROM players")))
    players.set_index('id',inplace=True)
    players = pd.DataFrame(db.execute(text("SELECT * FROM players")))
    players.set_index('id',inplace=True)
    def classdef(thing):
        class_years = []
        for thing in players['grad_year']:
            if isinstance(thing, Decimal):
                thing = int(thing)
            years_diff = math.ceil((date(thing, 9, 1) - date.today()).days / 365)
            if years_diff >= 5:
                return 5
            elif years_diff <1:
                return 0
            class_year = classdict.get(years_diff)
            class_years.append(class_year)
        players['class'] = class_years
    classdef(players['grad_year'])

    coaches = pd.DataFrame(db.execute(text("SELECT * FROM coaches")))
    coaches.set_index('id',inplace=True)

    notes = pd.DataFrame(db.execute(text("SELECT * FROM notes")))
    notes.set_index('id',inplace=True)

    players['full_name'] = players['first_name'] + ' ' + players['last_name']

    active_classes = ['Freshman','Sophomore','Junior','Senior']
    players['active'] = players['class'].isin(active_classes)

    #streamlit app

    st.title('Devon Prep Coaches App')
    st.subheader('Track Player Updates Below')
    ptoggle = st.toggle('Pitchers?')
    if ptoggle:
        fplayers = players.query('pitcher == True')[['first_name','last_name','class','level']]
    else:
        fplayers = players[['first_name','last_name','class','pos_1','pos_2','pos_3']].fillna('')
    fplayers

    #player notes

    st.title('Input New Player Note')
    currentplayers = players.query('active == True')

    with st.form(key='Input New Player Note'):
        note_pitcher = st.selectbox("Player", currentplayers['full_name'])
        note_date = st.date_input("Today's Date", value = "default_value_today")
        note_coach = st.selectbox("Coach", coaches['name'])
        note_note = st.text_input("Note")
        note_submit = st.form_submit_button(label = "Submit Note")

    if note_submit:
        new_note = {'pitcher': note_pitcher, 'date': note_date, 'coach': note_coach, 'note': note_note}
        pd.DataFrame([new_note])
        pnotes = pd.concat([notes, new_note], ignore_index=True)