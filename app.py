import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime

# Настройка страницы
st.set_page_config(
    page_title="Support Analytics Dashboard",
    layout="wide"
)

# Функция для загрузки данных
@st.cache_data
def load_data():
    with open('data.json', 'r') as file:
        data = json.load(file)
    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data['data'])
    # Конвертируем строковые даты в datetime
    df['call_datetime'] = pd.to_datetime(df['call_datetime'])
    df['call_end_time'] = pd.to_datetime(df['call_end_time'])
    df['response_time'] = pd.to_datetime(df['response_time'])
    return df

# Загрузка данных
try:
    df = load_data()
    
    # Заголовок
    st.title('📊 Support Analytics Dashboard')
    
    # Основные метрики в колонках
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Среднее время ответа
        wait_time = df['wait_time_seconds'].mean() / 60  # конвертируем в минуты
        st.metric(
            "Average Wait Time",
            f"{wait_time:.2f} min",
            delta="normal" if wait_time < 5 else "critical"
        )
    
    with col2:
        # Удовлетворенность клиентов
        satisfaction = df['satisfaction_score'].mean()
        st.metric(
            "Customer Satisfaction",
            f"{satisfaction:.1f}/5.0",
            delta="good" if satisfaction >= 4.5 else "needs improvement"
        )
    
    with col3:
        # Процент решенных обращений
        resolution_rate = (df['is_resolved'].sum() / len(df)) * 100
        st.metric(
            "Resolution Rate",
            f"{resolution_rate:.1f}%",
            delta="good" if resolution_rate > 90 else "needs attention"
        )
    
    # График распределения тем обращений
    st.subheader("📑 Distribution of Topics")
    topic_counts = df['topic'].value_counts()
    fig_topics = px.pie(
        values=topic_counts.values,
        names=topic_counts.index,
        title="Support Tickets by Topic"
    )
    st.plotly_chart(fig_topics)
    
    # График времени обработки
    st.subheader("⏱️ Call Duration Analysis")
    fig_duration = px.histogram(
        df,
        x='call_duration_seconds',
        nbins=20,
        title="Distribution of Call Durations"
    )
    fig_duration.update_layout(
        xaxis_title="Duration (seconds)",
        yaxis_title="Number of Calls"
    )
    st.plotly_chart(fig_duration)
    
    # Детальные данные
    st.subheader("📝 Detailed Data")
    st.dataframe(
        df[[
            'topic',
            'satisfaction_score',
            'call_duration_seconds',
            'is_resolved'
        ]]
    )

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.write("Please ensure your data.json file is properly formatted and accessible.")
