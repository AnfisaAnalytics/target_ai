import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from datetime import datetime
import json

# Настройка страницы
st.set_page_config(
    page_title="Анализ тикетов поддержки",
    page_icon="📊",
    layout="wide"
)

# Загрузка данных
@st.cache_data
def load_data():
    with open('data.json', 'r') as file:
        json_data = json.load(file)
    df = pd.DataFrame(json_data['data'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['closed_at'] = pd.to_datetime(df['closed_at'])
    return df

df = load_data()

# Заголовок
st.title('📊 Анализ тикетов поддержки')

# Боковая панель с фильтрами
st.sidebar.header('Фильтры')

# Фильтр по дате
date_range = st.sidebar.date_input(
    "Выберите период",
    [df['created_at'].min(), df['created_at'].max()]
)

# Фильтры по категориям
categories = st.sidebar.multiselect(
    'Категории',
    options=df['category'].unique(),
    default=df['category'].unique()
)

priorities = st.sidebar.multiselect(
    'Приоритеты',
    options=df['priority'].unique(),
    default=df['priority'].unique()
)

teams = st.sidebar.multiselect(
    'Команды',
    options=df['agent_team'].unique(),
    default=df['agent_team'].unique()
)

# Применение фильтров
mask = (
    (df['created_at'].dt.date >= date_range[0]) &
    (df['created_at'].dt.date <= date_range[1]) &
    (df['category'].isin(categories)) &
    (df['priority'].isin(priorities)) &
    (df['agent_team'].isin(teams))
)
filtered_df = df[mask]

# Основные метрики
st.header('Основные метрики')
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Всего тикетов", len(filtered_df))
with col2:
    st.metric("Среднее время ответа (ч)", 
              round(filtered_df['first_response_hours'].mean(), 2))
with col3:
    st.metric("Среднее время решения (ч)", 
              round(filtered_df['resolution_hours'].mean(), 2))
with col4:
    st.metric("Средняя оценка", 
              round(filtered_df['satisfaction_score'].mean(), 2))
with col5:
    st.metric("Процент эскалаций", 
              round((filtered_df['is_escalated'].sum() / len(filtered_df)) * 100, 2))

# Визуализации
st.header('Визуализации')

# Первый ряд графиков
col1, col2 = st.columns(2)

with col1:
    st.subheader('Время ответа по приоритетам')
    fig = px.box(filtered_df, x='priority', y='first_response_hours',
                 title='Время первого ответа по приоритетам')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader('Корреляционная матрица')
    correlation_matrix = filtered_df[['first_response_hours', 'resolution_hours', 
                                    'satisfaction_score', 'message_count']].corr()
    fig = px.imshow(correlation_matrix, 
                    text=correlation_matrix.round(2),
                    aspect='auto',
                    color_continuous_scale='RdBu')
    st.plotly_chart(fig, use_container_width=True)

# Второй ряд графиков
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader('Распределение по приоритетам')
    fig = px.pie(filtered_df, names='priority',
                 title='Распределение тикетов по приоритетам')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader('Распределение по категориям')
    fig = px.pie(filtered_df, names='category',
                 title='Распределение тикетов по категориям')
    st.plotly_chart(fig, use_container_width=True)

with col3:
    st.subheader('Распределение по командам')
    fig = px.pie(filtered_df, names='agent_team',
                 title='Распределение тикетов по командам')
    st.plotly_chart(fig, use_container_width=True)

# Таблица с данными
st.header('Детальные данные')
st.dataframe(
    filtered_df.sort_values('created_at', ascending=False),
    use_container_width=True
)
