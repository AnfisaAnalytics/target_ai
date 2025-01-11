import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta


import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="DDx",
    page_icon="📊",
    layout="wide"
)

# Enhanced CSS with explicit background colors and more specific selectors
st.markdown("""
    <style>
        /* Reset background colors for all major containers */
        .stApp {
            background-color: white !important;
        }
        .st-emotion-cache-z5fcl4{
        padding:1rem 1rem;}
        .main {
            background-color: white !important;
        }
        
        body {
            background-color: white !important;
        }
        
        .metric-card {
            background-color: #f8f9fa !important;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        
        .chart-container {
            background-color: white !important;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            margin-bottom: 2rem;
        }
        
        div.stButton > button {
            background-color: #f8f9fa !important;
            border: 1px solid #dee2e6;
            padding: 0.5rem 1rem;
            margin-right: 0.5rem;
        }
        
        div.stButton > button:hover {
            background-color: #e9ecef !important;
            border-color: #dee2e6;
        }
        
        div.stButton > button:focus {
            background-color: #0d6efd !important;
            color: white;
            border-color: #0d6efd;
        }
        
        /* Force white background on plot containers */
        .js-plotly-plot {
            background-color: white !important;
        }
        
        /* Additional reset for any inherited backgrounds */
        [data-testid="stAppViewContainer"] {
            background-color: white !important;
        }
        
        [data-testid="stHeader"] {
            background-color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Convert the data list to DataFrame
    df = pd.DataFrame(json_data['data'])
    
    # Convert datetime columns
    datetime_cols = ['Дата и время звонка', 'Время ответа', 'Дата и время решения вопроса']
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])
    
    # Calculate response and resolution times in minutes
    df['Response Time (min)'] = (df['Время ответа'] - df['Дата и время звонка']).dt.total_seconds() / 60
    df['Resolution Time (min)'] = (df['Дата и время решения вопроса'] - df['Дата и время звонка']).dt.total_seconds() / 60
    
    return df

def filter_data_by_timerange(df, timerange):
    now = datetime.now()
    if timerange == "Today":
        start_date = now - timedelta(days=1)
    elif timerange == "Last Week":
        start_date = now - timedelta(days=7)
    elif timerange == "Last Month":
        start_date = now - timedelta(days=30)
    elif timerange == "Last Year":
        start_date = now - timedelta(days=365)
    else:  # All Data
        return df
    
    return df[df['Дата и время звонка'] >= start_date]

def main():
    st.title("🎯 Support Service Analytics Dashboard")
    st.markdown("### Real-time analytics for customer support performance")
    
    try:
        # Load data
        df = load_data('data.json')
        
        # Time range filter buttons
        st.markdown("### Select Time Range")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Initialize session state for active button if it doesn't exist
        if 'active_timerange' not in st.session_state:
            st.session_state.active_timerange = "All Data"
        
        # Create buttons for each time range
        if col1.button("Today", type="primary" if st.session_state.active_timerange == "Today" else "secondary"):
            st.session_state.active_timerange = "Today"
        if col2.button("Last Week", type="primary" if st.session_state.active_timerange == "Last Week" else "secondary"):
            st.session_state.active_timerange = "Last Week"
        if col3.button("Last Month", type="primary" if st.session_state.active_timerange == "Last Month" else "secondary"):
            st.session_state.active_timerange = "Last Month"
        if col4.button("Last Year", type="primary" if st.session_state.active_timerange == "Last Year" else "secondary"):
            st.session_state.active_timerange = "Last Year"
        if col5.button("All Data", type="primary" if st.session_state.active_timerange == "All Data" else "secondary"):
            st.session_state.active_timerange = "All Data"
        
        # Filter data based on selected time range
        filtered_df = filter_data_by_timerange(df, st.session_state.active_timerange)
        
        # Calculate metrics
        metrics = {
            'avg_response_time': filtered_df['Response Time (min)'].mean(),
            'avg_resolution_time': filtered_df['Resolution Time (min)'].mean(),
            'resolution_rate': (filtered_df['Решение вопроса'].mean() * 100),
            'avg_satisfaction': filtered_df['Оценка удовлетворённости'].mean()
        }
        
        # Replace the visualization section with this code:

        # First row of charts - Response Time and Service Distribution
        col1, col2 = st.columns([0.7, 0.3])  # 70% and 30% width ratio
        
        with col1:
            st.subheader("Response Time Analysis")
            fig_response = px.bar(
                filtered_df,
                x='Услуга',
                y='Response Time (min)',
                color='Тема звонка',
                title="Response Time by Service and Topic"
            )
            st.plotly_chart(fig_response, use_container_width=True)
        
        with col2:
            st.subheader("Service Distribution")
            fig_service = px.pie(
                filtered_df,
                names='Услуга',
                title="Distribution of Services"
            )
            st.plotly_chart(fig_service, use_container_width=True)
        
        # Second row of charts - Satisfaction Distribution and another metric
        col3, col4 = st.columns([0.4, 0.6])  # 40% and 60% width ratio
        
        with col3:
            st.subheader("Satisfaction Distribution")
            fig_satisfaction = px.histogram(
                filtered_df,
                x='Оценка удовлетворённости',
                title="Distribution of Satisfaction Scores",
                nbins=5
            )
            st.plotly_chart(fig_satisfaction, use_container_width=True)
        
        with col4:
            st.subheader("Resolution Time Analysis")
            fig_resolution = px.line(
                filtered_df,
                x='Дата и время звонка',
                y='Resolution Time (min)',
                title="Resolution Time Trend"
            )
            st.plotly_chart(fig_resolution, use_container_width=True)

        # Data table
        st.subheader("Detailed Data View")
        st.dataframe(
            filtered_df[[
                'Услуга', 'Тема звонка', 'Response Time (min)',
                'Resolution Time (min)', 'Оценка удовлетворённости', 'Решение вопроса'
            ]],
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Error loading or processing data: {str(e)}")

if __name__ == "__main__":
    main()
