import pandas as pd
import streamlit as st

def authenticate():
    st.sidebar.header('Login')
    password = st.sidebar.text_input("Password", type='password')

    if password == "db_dp_baseball":
        return True
    elif password:
        st.sidebar.error("Incorrect password")
    return False

if authenticate():
    st.write(f"Welcome {name}!")

    players = pd.read_excel(r"C:\Users\dbann\Documents\Baseball\code\Devon Prep\Devon Prep Baseball.xlsx")

    #clean column names

    def clean_column_names(columns):
        return ['is_pitcher' if col == 'Pitcher?' else col.lower().replace(' ', '_') for col in columns]

    players.columns = clean_column_names(players.columns)

    players['full_name'] = players['first_name'] + ' ' + players['last_name']

    active_classes = ['Freshman','Sophomore','Junior','Senior']
    players['active'] = players['class'].isin(active_classes)

    pnotes = pd.DataFrame(columns = ['pitcher','date','author','note'])

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
        pnotes = pnotes.append(new_note, ignore_index=True)