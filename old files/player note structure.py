## Display Coach Notes

st.subheader("Coach Notes")
type_select = st.multiselect("Type",options=note_types,default=note_types)

# Merge coach names onto table
notes_display = notes.merge(coaches, left_on='coach_id', right_index=True, how='left').merge(players,left_on='player_id',right_index=True,how='left')

notes_display = notes_display.drop(['coach_id'], axis=1)

filtered_notes = notes_display[notes_display['player_id'] == player_select]

notes_table = filtered_notes[filtered_notes['type'].isin(type_select)]

notes_table.rename(columns={
    'full_name': 'Player',
    'type': 'Type',
    'name': 'Coach',
    'note': 'Note',
    'date': 'Date'
}, inplace=True)

st.dataframe(notes_table[['Player','Type','Date','Coach','Note']],hide_index=True)

# # Get video rows for this player, sorted by most recent
# def display_video():
#     player_name = player_options[player_select]  # Get the player name from player_options
#     player_videos = video[video['player_id'] == player_select]
#     for index, row in player_videos.iterrows():
#         st.write(f"{row['date']} - {player_name} - {row['speed']} - {row['pitch_type']}")
#         st.video(row['url'])

# st.subheader("Video:")
# display_video()