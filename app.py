import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
import numpy as np

# Custom CSS styling
st.set_page_config(
    page_title="Support Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
    <style>
        /* Main content styling */
        .main {
            padding: 2rem;
        }
        
        /* Header styling */
        .st-emotion-cache-10trblm e1nzilvr1 {
            color: red;
            font-size: 105rem !important;
            font-weight: 700 !important;
            padding-bottom: 1rem;
            border-bottom: 2px solid #1E88E5;
            margin-bottom: 2rem;
        }
        
        /* Subheader styling */
        .css-1outpf7 {
            color: #424242;
            font-size: 1.5rem !important;
            padding-top: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Metric containers */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            color: #1E88E5 !important;
            font-weight: 700 !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 1rem !important;
            color: #616161 !important;
        }
        
        /* Card-like styling for metrics */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        
        /* Filter widgets styling */
        .stSelectbox label, .stMultiSelect label {
            color: #424242;
            font-weight: 600;
        }
        
        /* Chart containers */
        .stPlotlyChart {
            background-color: #ffffff;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        
        /* Custom theme colors */
        :root {
            --primary-color: #1E88E5;
            --background-color: #f8f9fa;
            --text-color: #424242;
        }
    </style>
""", unsafe_allow_html=True)

# Load and prepare data
@st.cache_data
def load_data():
    with open('data.json', 'r') as file:
        json_data = json.load(file)
    df = pd.DataFrame(json_data['data'])
    
    # Convert dates
    date_columns = ['created_at', 'first_response_at', 'resolved_at']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col])
    
    # Calculate resolution hours
    df['resolution_hours'] = (df['resolved_at'] - df['created_at']).dt.total_seconds() / 3600
    return df

df = load_data()

# Sidebar with custom styling
st.sidebar.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1 style='color: #1E88E5; font-size: 1.5rem; font-weight: 700;'>🎛️ jhjjjhj управления</h1>
    </div>
""", unsafe_allow_html=True)

# Date range filter with custom styling
st.sidebar.markdown("### 📅 Период")
date_range = st.sidebar.date_input(
    "",  # Empty label as we use markdown above
    [df['created_at'].min().date(), df['created_at'].max().date()]
)

# Team filter with custom styling
st.sidebar.markdown("### 👥 Команды")
selected_teams = st.sidebar.multiselect(
    '',  # Empty label as we use markdown above
    options=df['agent_team'].unique(),
    default=df['agent_team'].unique()
)

# Category filter with custom styling
st.sidebar.markdown("### 📊 Категории")
selected_categories = st.sidebar.multiselect(
    '',  # Empty label as we use markdown above
    options=df['category'].unique(),
    default=df['category'].unique()
)

# Apply filters
mask = (
    (df['created_at'].dt.date >= date_range[0]) &
    (df['created_at'].dt.date <= date_range[1]) &
    (df['agent_team'].isin(selected_teams)) &
    (df['category'].isin(selected_categories))
)
filtered_df = df[mask]

# Main dashboard with styled title
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1E88E5; font-size: 2.5rem; font-weight: 700;'>📊 Дашборд поддержки</h1>
    </div>
""", unsafe_allow_html=True)

# KPI metrics with enhanced styling
st.markdown("<div style='padding: 1rem 0;'>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "⏱️ Среднее время первого ответа",
        f"{filtered_df['first_response_hours'].mean():.2f}ч"
    )

with col2:
    st.metric(
        "⌛ Среднее время разрешения",
        f"{filtered_df['resolution_hours'].mean():.2f}ч"
    )

with col3:
    st.metric(
        "⭐ Средняя оценка",
        f"{filtered_df['satisfaction_score'].mean():.2f}"
    )

with col4:
    high_satisfaction = (len(filtered_df[filtered_df['satisfaction_score'] >= 4]) / len(filtered_df)) * 100
    st.metric(
        "📈 % высоких оценок (4-5)",
        f"{high_satisfaction:.1f}%"
    )
st.markdown("</div>", unsafe_allow_html=True)

# Styled visualizations
st.markdown("### 📊 Распределение времени первого ответа по командам")
fig1 = px.box(
    filtered_df,
    x='agent_team',
    y='first_response_hours',
    color='agent_team',
    template='plotly_white'
)
fig1.update_layout(
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(t=40, b=40, l=40, r=40),
    font=dict(family="Arial, sans-serif", size=12)
)
st.plotly_chart(fig1, use_container_width=True)

# Styled heatmap
st.markdown("### 🌡️ Тепловая карта обращений")
filtered_df['hour'] = filtered_df['created_at'].dt.hour
filtered_df['weekday'] = filtered_df['created_at'].dt.day_name()
hourly_data = pd.crosstab(filtered_df['weekday'], filtered_df['hour'])

fig2 = go.Figure(data=go.Heatmap(
    z=hourly_data.values,
    x=hourly_data.columns,
    y=hourly_data.index,
    colorscale='Viridis'
))
fig2.update_layout(
    xaxis_title='Час дня',
    yaxis_title='День недели',
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(t=40, b=40, l=40, r=40),
    font=dict(family="Arial, sans-serif", size=12)
)
st.plotly_chart(fig2, use_container_width=True)

# Styled satisfaction funnel
st.markdown("### 🎯 Воронка удовлетворенности")
satisfaction_funnel = filtered_df['satisfaction_score'].value_counts().sort_index(ascending=False)

fig3 = go.Figure(go.Funnel(
    y=['5 звезд ⭐⭐⭐⭐⭐', '4 звезды ⭐⭐⭐⭐', '3 звезды ⭐⭐⭐', '2 звезды ⭐⭐', '1 звезда ⭐'],
    x=satisfaction_funnel.values,
    textinfo="value+percent initial",
    marker=dict(color=['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336'])
))
fig3.update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(t=40, b=40, l=40, r=40),
    font=dict(family="Arial, sans-serif", size=12)
)
st.plotly_chart(fig3, use_container_width=True)

# Styled additional metrics
st.markdown("### 📈 Дополнительные метрики")
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "⏱️ Медианное время первого ответа",
        f"{filtered_df['first_response_hours'].median():.2f}ч"
    )
    st.metric(
        "⌛ 90-й перцентиль времени разрешения",
        f"{filtered_df['resolution_hours'].quantile(0.9):.2f}ч"
    )

with col2:
    st.metric(
        "👎 Тикеты с низкой оценкой (1-2)",
        len(filtered_df[filtered_df['satisfaction_score'] <= 2])
    )
    st.metric(
        "💬 Среднее кол-во сообщений",
        f"{filtered_df['message_count'].mean():.1f}"
    )
