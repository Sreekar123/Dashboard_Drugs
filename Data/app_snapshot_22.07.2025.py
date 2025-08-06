#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px


#######################
# Dummy data for table
dummy_data = {
    "S No.": [1, 2, 3, 4, 5],
    "Item Code": ["D001", "D002", "D003", "D004", "D005"],
    "Item Name": ["Paracetamol", "Amoxicillin", "Ciprofloxacin", "Ibuprofen", "Azithromycin"],
    "Stock on Hand": [2500, 1300, 800, 1600, 400],
    "Pending Supply": [500, 200, 0, 400, 600],
    "RC Status": ["Active", "Pending", "Expired", "Active", "Pending"],
    "Stock Suff. Months": [3.2, 1.5, 0.8, 2.0, 0.6],
    "Stock + Pending Supply Suff. Months": [4.0, 1.8, 0.8, 2.5, 1.4]
}

df_dummy = pd.DataFrame(dummy_data)

#######################
# Page configuration
st.set_page_config(
    page_title="Dashboard for Drugs",
    # page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.metric-box {
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 10px;
    text-align: center;
    font-weight: bold;
    font-size: 18px;
}
.lightblue { background-color: #D6EAF8; }
.lightgreen { background-color: #D5F5E3; }
.lightyellow { background-color: #FCF3CF; }
.lightred { background-color: #F5B7B1; }
</style>
""", unsafe_allow_html=True)


#######################
# Load data
df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')


#######################
# Sidebar
with st.sidebar:
    st.title('Dashboard for Drugs')
    
    year_list = list(df_reshaped.year.unique())[::-1]
    
    selected_year = st.selectbox('Select a year', year_list)
    df_selected_year = df_reshaped[df_reshaped.year == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="population", ascending=False)

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

    options_list = ['All Drugs', 'Priority Drugs']
    selected_category = st.selectbox('Option to select', options_list)


#######################
# Plots

# Heatmap
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
            y=alt.Y(f'{input_y}:O', axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
            color=alt.Color(f'max({input_color}):Q',
                             legend=None,
                             scale=alt.Scale(scheme=input_color_theme)),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
        ).properties(width=900
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        ) 
    # height=300
    return heatmap

# Choropleth map
def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(input_df, locations=input_id, color=input_column, locationmode="USA-states",
                               color_continuous_scale=input_color_theme,
                               range_color=(0, max(df_selected_year.population)),
                               scope="usa",
                               labels={'population':'Population'}
                              )
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth


# Donut chart
def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text

# Convert population to text 
def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

# Calculation year-over-year population migrations
def calculate_population_difference(input_df, input_year):
  selected_year_data = input_df[input_df['year'] == input_year].reset_index()
  previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
  selected_year_data['population_difference'] = selected_year_data.population.sub(previous_year_data.population, fill_value=0)
  return pd.concat([selected_year_data.states, selected_year_data.id, selected_year_data.population, selected_year_data.population_difference], axis=1).sort_values(by="population_difference", ascending=False)


#######################
# Dashboard Main Panel
#######################
# Dashboard Main Panel (Updated to 3 Rows)

st.markdown('### Stock Position of Drugs')

# Metrics Row (Row 1)
metric_cols = st.columns(5)

with metric_cols[0]:
    df_population_difference_sorted = calculate_population_difference(df_reshaped, selected_year)

    if selected_year > 2010:
        first_state_name = df_population_difference_sorted.states.iloc[0]
        first_state_population = format_number(df_population_difference_sorted.population.iloc[0])
        first_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[0])
    else:
        first_state_name = '-'
        first_state_population = '-'
        first_state_delta = ''

    #st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)

    st.markdown(f"""
    <div class="metric-box lightblue">
        {"Total Drugs"}<br>
        <span style="font-size: 24px;">{first_state_population}</span><br>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[1]:
    if selected_year > 2010:
        last_state_name = df_population_difference_sorted.states.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.population.iloc[-1])
        last_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''
        
    st.markdown(f"""
    <div class="metric-box lightgreen">
        {"> 3 months"}<br>
        <span style="font-size: 24px;">{first_state_population}</span><br>
        <span style="color: green;">{first_state_delta}</span>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[2]:
    if selected_year > 2010:
        last_state_name = df_population_difference_sorted.states.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.population.iloc[-1])
        last_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''

    st.markdown(f"""
    <div class="metric-box lightyellow">
        {"1-3 months"}<br>
        <span style="font-size: 24px;">{first_state_population}</span><br>
        <span style="color: green;">{first_state_delta}</span>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[3]:
    if selected_year > 2010:
        last_state_name = df_population_difference_sorted.states.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.population.iloc[-1])
        last_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''

    st.markdown(f"""
    <div class="metric-box lightred">
        {"< 1 month"}<br>
        <span style="font-size: 24px;">{first_state_population}</span><br>
        <span style="color: green;">{first_state_delta}</span>
    </div>
    """, unsafe_allow_html=True)

with metric_cols[4]:
    if selected_year > 2010:
        last_state_name = df_population_difference_sorted.states.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.population.iloc[-1])
        last_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''

    st.markdown(f"""
    <div class="metric-box lightred">
        {"No Stock"}<br>
        <span style="font-size: 24px;">{first_state_population}</span><br>
        <span style="color: green;">{first_state_delta}</span>
    </div>
    """, unsafe_allow_html=True)

# Visualizations Row (Row 2)
st.markdown("### Showing ____ drugs")

# Use st.dataframe for scrollable table with smaller size
st.dataframe(
    df_dummy,
    use_container_width=True,
    hide_index=True,
    height=230  # adjust height to your layout
)


# Table + About (Row 3)
st.markdown('### 📊 Top States by Population')

st.dataframe(df_selected_year_sorted,
             column_order=("states", "population"),
             hide_index=True,
             width=None,
             column_config={
                "states": st.column_config.TextColumn("States"),
                "population": st.column_config.ProgressColumn(
                    "Population",
                    format="%f",
                    min_value=0,
                    max_value=max(df_selected_year_sorted.population),
                )}
             )

with st.expander('About', expanded=True):
    st.write('''
        - Data: [U.S. Census Bureau](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-state-total.html).
        - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
        - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
    ''')
    
    with st.expander('About', expanded=True):
        st.write('''
            - Data: [U.S. Census Bureau](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-state-total.html).
            - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
            - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
            ''')