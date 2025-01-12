import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import numpy as np
import json

# Настройка конфигурации страницы
# layout="wide" - разворачивает контент на всю ширину
# initial_sidebar_state="expanded" - боковая панель развернута при запуске
st.set_page_config(
    page_title="Центр поддержки - Аналитика",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Функция загрузки и подготовки данных
# @st.cache_data - кэширует результат для оптимизации производительности
@st.cache_data
def load_data():
    try:
        # Открываем JSON файл и загружаем данные
        with open('data.json', 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        df = pd.DataFrame(json_data['data'])
        
        # Преобразуем строковые даты в datetime объекты
        date_columns = ["Дата и время звонка", "Время ответа", "Дата и время решения вопроса"]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col])
        
        # Добавляем вычисляемые колонки
        df['День недели'] = df['Дата и время звонка'].dt.day_name()  # Название дня недели
        df['Час'] = df['Дата и время звонка'].dt.hour  # Час из времени звонка
        # Вычисляем время ожидания в минутах
        df['Время ожидания'] = (df['Время ответа'] - df['Дата и время звонка']).dt.total_seconds() / 60
        
        return df
    except FileNotFoundError:
        st.error("Файл data.json не найден!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {str(e)}")
        return pd.DataFrame()

# Функция фильтрации данных по временному периоду
def filter_data_by_timeframe(df, timeframe):
    now = pd.Timestamp.now()
    if timeframe == "Сегодня":
        return df[df['Дата и время звонка'].dt.date == now.date()]
    elif timeframe == "Неделя":
        week_ago = now - timedelta(days=7)
        return df[df['Дата и время звонка'] >= week_ago]
    elif timeframe == "Месяц":
        month_ago = now - timedelta(days=30)
        return df[df['Дата и время звонка'] >= month_ago]
    elif timeframe == "Год":
        year_ago = now - timedelta(days=365)
        return df[df['Дата и время звонка'] >= year_ago]
    else:  # "Все данные"
        return df

# Функция расчета KPI
def calculate_kpis(df):
    if df.empty:
        return {
            "repeat_percentage": 0.0,
            "avg_wait_time": 0.0,
            "lost_calls": 0,
            "cost_per_call": 500,
            "after_hours_percentage": 0.0
        }
    
    # Расчет процента повторяющихся запросов
    total_requests = len(df)
    repeated_requests = df['Тема звонка'].value_counts()
    repeated_requests = repeated_requests[repeated_requests > 1].sum()
    repeat_percentage = (repeated_requests / total_requests) * 100
    
    # Расчет среднего времени ожидания
    avg_wait_time = df['Время ожидания'].mean()
    
    # Подсчет потерянных звонков (время ожидания > 30 минут)
    lost_calls = len(df[df['Время ожидания'] > 30])
    
    # Фиксированная стоимость обращения
    cost_per_call = 500
    
    # Расчет процента запросов вне рабочего времени
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
    
    # Кнопки выбора временного периода
    time_periods = ["Сегодня", "Неделя", "Месяц", "Год", "Все данные"]
    selected_period = st.radio("Выберите период:", time_periods, horizontal=True)
    
    # Фильтрация данных по выбранному периоду
    filtered_df = filter_data_by_timeframe(df, selected_period)
    
    if filtered_df.empty:
        st.warning(f"Нет данных за выбранный период: {selected_period}")
        return
        
    kpis = calculate_kpis(filtered_df)
    
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
    
    # CSS для управления отступами и высотой
    st.markdown("""
        <style>
        .st-emotion-cache-1yiq2ps{
        background:#f9fafd;}
        
            .stColumn {
                padding: 0.5rem;
                height: 100%;
            }
            .element-container {
                margin: 0.5rem 0;
            }
            /* Настройка высоты графиков */
            .chart-container {
                height: 400px;  /* Базовая высота для графиков */
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Основные колонки
    left_col, right_col = st.columns([1, 1])
    
    # Левая колонка (тепловая карта и сводная таблица)
    with left_col:
        # Тепловая карта
        st.subheader("Объем обращений")
        heatmap_data = pd.crosstab(filtered_df['День недели'], filtered_df['Час'])
        fig_heatmap = px.imshow(heatmap_data,
                               labels=dict(x="Час", y="День недели", color="Количество обращений"),
                               aspect="auto",
                               color_continuous_scale="Blues")
        # Настройка высоты тепловой карты
        fig_heatmap.update_layout(height=400)  # Можно изменить значение для настройки высоты
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Сводная таблица
        st.subheader("Анализ потенциала внедрения AI")
        ai_potential = pd.DataFrame({
            'Метрика': ['% типовых запросов', 'Среднее время ожидания', 'Операторов в смену', 
                       'Доступность поддержки', 'Стоимость обработки'],
            'Значение': [f"{kpis['repeat_percentage']}%", 
                        f"{kpis['avg_wait_time']} мин", 
                        "5",
                        f"{100 - kpis['after_hours_percentage']}%",
                        f"{kpis['cost_per_call']} ₽"]
        })
        st.table(ai_potential)
    
    # Правая колонка (остальные визуализации)
    with right_col:
        # Настройки высоты графиков
         
        # Распределение запросов "Высота графиков 
        st.subheader("Распределение запросов")
        fig_pie = px.pie(filtered_df, names='Тема звонка')
        fig_pie.update_layout(height=222)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # График времени ожидания
        st.subheader("Время ожидания")
        fig_line = px.line(filtered_df.groupby('Час')['Время ожидания'].mean().reset_index(),
                          x='Час', y='Время ожидания')
        fig_line.update_layout(height=300)
        st.plotly_chart(fig_line, use_container_width=True)
        
        # График удовлетворенности
        st.subheader("Удовлетворенность")
        satisfaction_data = filtered_df['Оценка удовлетворённости'].value_counts().sort_index()
        fig_bar = px.bar(satisfaction_data)
        fig_bar.update_layout(height=450)
        st.plotly_chart(fig_bar, use_container_width=True)

if __name__ == "__main__":
    main()
