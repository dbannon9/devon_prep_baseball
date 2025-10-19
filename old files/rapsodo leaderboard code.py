#%% Creating Rapsodo Leaderboards

## Hitting

# merge for id purposes
raphit = rapsodo_hitting.merge(players_show,left_on='Player ID', right_on='rapsodo_id', how='left')
raphit['ExitVelocity'] = pd.to_numeric(raphit['ExitVelocity'], errors='coerce')[raphit['ExitVelocity']!="-"]

# group by id
raphit_group = raphit.groupby('rapsodo_id').agg(
    ExitVelocity_max=('ExitVelocity', 'max'),
    ExitVelocity_avg=('ExitVelocity', 'mean'),
    ExitVelocity_90th_percentile=('ExitVelocity', lambda x: np.percentile(x, 90))
).reset_index()

# join full_name back on
raphit_group = raphit_group.merge(
    players_show[['rapsodo_id', 'full_name']], 
    on='rapsodo_id', 
    how='left'
)

# col rename
raphit_group.rename(columns={
    'full_name': 'Player',
    'ExitVelocity_max': 'Max EV',
    'ExitVelocity_avg': 'Average EV',
    'ExitVelocity_90th_percentile': '90th pct EV',
}, inplace=True)

# sort
raphit_group.sort_values(by='Average EV', ascending=False, inplace=True)

# # color gradient
# def highlight_ev(df):
#     return df.style.background_gradient(
#         cmap='coolwarm',
#         subset=['Max EV', 'Average EV', '90th pct EV']
#     ).format({'Max EV': '{:.1f}', 'Average EV': '{:.1f}', '90th pct EV': '{:.1f}'})

# # display
# st.subheader("Rapsodo Leaderboard")
# st.dataframe(
#     highlight_ev(raphit_group[['Player', 'Average EV', '90th pct EV', 'Max EV']]),
#     hide_index=True,
# )


# Define custom colormap (deep navy replacing white)
colors = ["blue", "black", "red"]  # Adjust as needed
custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom_coolwarm", colors)

# Function to apply color gradient
def highlight_ev(df):
    return df.style.background_gradient(
        cmap=custom_cmap,  # Use the custom colormap
        subset=['Max EV', 'Average EV', '90th pct EV']
    ).format({'Max EV': '{:.1f}', 'Average EV': '{:.1f}', '90th pct EV': '{:.1f}'})

# Display leaderboard
st.subheader("Rapsodo Leaderboard")
st.dataframe(
    highlight_ev(raphit_group[['Player', 'Average EV', '90th pct EV', 'Max EV']]),
    hide_index=True,
)


