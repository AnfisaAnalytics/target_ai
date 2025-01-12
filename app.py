import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time
import numpy as np
import json

# Set page configuration
st.set_page_config(
    page_title="Центр поддержки - Аналитика",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to load and prepare data
@st.cache_data
def load_data():
    try:
        # Загрузка данных из JSON файла
        with open('data.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        # Создание DataFrame из данных
        df = pd.DataFrame(json_data['data'])
        
        # Преобразование строковых дат в datetime
        date_columns = ["Дата и время звонка", "Время ответа", "Дата и время решения вопроса"]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col])
        
        # Добавление дополнительных колонок для анализа
        df['День недели'] = df['Дата и время звонка'].dt.day_name()
        df['Час'] = df['Дата и время звонка'].dt.hour
        df['Время ожидания'] = (df['Время ответа'] - df['Дата и время звонка']).dt.total_seconds() / 60
        
        return df
    except FileNotFoundError:
        st.error("Файл data.json не найден!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {str(e)}")
        return pd.DataFrame()

# Функции для расчета KPI
def calculate_kpis(df):
    if df.empty:
        return {
            "repeat_percentage": 0.0,
            "avg_wait_time": 0.0,
            "lost_calls": 0,
            "cost_per_call": 500,
            "after_hours_percentage": 0.0
        }
    
    # 1. Процент повторяющихся запросов
    total_requests = len(df)
    repeated_requests = df['Тема звонка'].value_counts()
    repeated_requests = repeated_requests[repeated_requests > 1].sum()
    repeat_percentage = (repeated_requests / total_requests) * 100
    
    # 2. Среднее время ожидания
    avg_wait_time = df['Время ожидания'].mean()
    
    # 3. Потерянные обращения (считаем, если время ожидания > 30 минут)
    lost_calls = len(df[df['Время ожидания'] > 30])
    
    # 4. Стоимость обращения (условно берем 500 рублей)
    cost_per_call = 500
    
    # 5. Процент запросов в нерабочее время
    def is_working_hours(hour):
        return 9 <= hour <= 18
    
    after_hours = len(df[~df['Час'].apply(is_working_hours)])
    after_hours_percentage = (after_hours / total_requests) * 100
    
    return {
        "repeat_percentage": round(repeat_percentage, 1),
        "avg_wait_time": round(avg_wait_time, 1),
        "lost_calls": lost_calls,
        "cost_per_call": cost_per_call,
        "after_hours_percentage": round(after_hours_percentage, 1)
    }

# Основной интерфейс
def main():
    st.title("📊 Аналитика центра поддержки")
    
    # Загрузка данных
    df = load_data()
    
    if df.empty:
        st.warning("Нет данных для отображения")
        return
        
    kpis = calculate_kpis(df)
    
    # KPI секция
    st.header("Ключевые показатели")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Повторяющиеся запросы", f"{kpis['repeat_percentage']}%")
    with col2:
        st.metric("Среднее время ожидания", f"{kpis['avg_wait_time']} мин")
    with col3:
        st.metric("Потерянные обращения", kpis['lost_calls'])
    with col4:
        st.metric("Стоимость обращения", f"{kpis['cost_per_call']} ₽")
    with col5:
        st.metric("Запросы вне рабочих часов", f"{kpis['after_hours_percentage']}%")
    
    # Визуализации
    st.header("Детальный анализ")
    
    # 1. Тепловая карта обращений
    st.subheader("Объем обращений по времени суток и дням недели")
    heatmap_data = pd.crosstab(df['День недели'], df['Час'])
    fig_heatmap = px.imshow(heatmap_data,
                           labels=dict(x="Час", y="День недели", color="Количество обращений"),
                           aspect="auto",
                           color_continuous_scale="Blues")
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 2. Распределение запросов
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Распределение запросов по категориям")
        fig_pie = px.pie(df, names='Тема звонка', 
                        title="Распределение запросов")
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Время ожидания в течение дня")
        fig_line = px.line(df.groupby('Час')['Время ожидания'].mean().reset_index(),
                          x='Час', y='Время ожидания',
                          title="Среднее время ожидания по часам")
        st.plotly_chart(fig_line, use_container_width=True)
    
    # 3. Причины неудовлетворенности
    st.subheader("Анализ неудовлетворенности клиентов")
    satisfaction_data = df['Оценка удовлетворённости'].value_counts().sort_index()
    fig_bar = px.bar(satisfaction_data,
                     title="Распределение оценок удовлетворенности")
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Сводная таблица
    st.header("Анализ потенциала внедрения AI")
    ai_potential = pd.DataFrame({
        'Метрика': ['% типовых запросов', 'Среднее время ожидания', 'Операторов в смену', 'Доступность поддержки', 'Стоимость обработки'],
        'Значение': [f"{kpis['repeat_percentage']}%", 
                    f"{kpis['avg_wait_time']} мин", 
                    "5", # Условное значение
                    f"{100 - kpis['after_hours_percentage']}%",
                    f"{kpis['cost_per_call']} ₽"]
    })
    st.table(ai_potential)

if __name__ == "__main__":
    main()
