import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

db = create_engine("postgresql://postgres.xtmfmfkpgommfdujhvev:G#v2!*hq8hU8-aU@aws-0-us-east-1.pooler.supabase.com:6543/postgres").connect()

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

###### PICK UP HERE, ADD IN CLASS AND OTHER FORMULA COLUMNS ######
    
    coaches = pd.DataFrame(db.execute(text("SELECT * FROM coaches")))
    coaches.set_index('id',inplace=True)

    notes = pd.DataFrame(db.execute(text("SELECT * FROM notes")))
    notes.set_index('id',inplace=True)

    #clean column names
    def clean_column_names(columns):
        return ['is_pitcher' if col == 'Pitcher?' else col.lower().replace(' ', '_') for col in columns]

    players.columns = clean_column_names(players.columns)

    players['full_name'] = players['first_name'] + ' ' + players['last_name']

    active_classes = ['Freshman','Sophomore','Junior','Senior']
    players['active'] = players['class'].isin(active_classes)

    pnotes = pd.read_csv("https://raw.githubusercontent.com/dbannon9/devon_prep_baseball/master/pnotes.csv")

    #streamlit app

    st.title('Devon Prep Coaches App')
    st.subheader('Track Player Updates Below')
    ptoggle = st.toggle('Pitchers?')
    if ptoggle:
        fplayers = players.query('is_pitcher == True')[['first_name','last_name','class','level']]
    else:
        fplayers = players[['first_name','last_name','class','level','position_1','position_2','position_3']].fillna('')
    fplayers

    #pitcher notes

    st.title('Input New Pitcher Note')
    currentpitchers = players.query('is_pitcher == True').query('active == True')
    authors = ['Coach Palumbo','Coach Grande','Coach Bannon','Coach Martin','Coach Toal','Coach Kania']

    with st.form(key='Input New Pitcher Note'):
        pnote_pitcher = st.selectbox("Pitcher", currentpitchers['full_name'])
        pnote_date = st.date_input("Today's Date", value = "default_value_today")
        pnote_author = st.selectbox("Author", authors)
        pnote_note = st.text_input("Note")
        pnote_submit = st.form_submit_button(label = "Submit Note")

    if pnote_submit:
        new_note = {'pitcher': pnote_pitcher, 'date': pnote_date, 'author': pnote_author, 'note': pnote_note}
        pd.DataFrame([new_note])
        pnotes = pd.concat([pnotes, new_note], ignore_index=True)