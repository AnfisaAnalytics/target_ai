import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta

# Настройка цветовой палитры
color_palette = ['rgba(239, 132, 50, 0.7)', 'rgba(46, 96, 107, 0.7)', 
                'rgba(4, 21, 35, 0.7)', 'rgba(111, 46, 24, 0.7)', 
                'rgba(122, 85, 86, 0.7)', 'rgba(146, 151, 172, 0.7)']

# Конфигурация страницы
st.set_page_config(
    page_title="Аналитика поддержки",
    page_icon="📊",
    layout="wide"
)

# Обновленные стили CSS
st.markdown("""
    <style>
        /* Основные контейнеры */
        .stApp {
            background-color: #f0f2f6 !important;
        }
        
        .main {
            padding: 1rem 2rem !important;
        }
        .stMetric, .element-container, .stDataFrame{
        box-shadow:0 2px 4px rgba(0,0,0,0) !important;
        }
        /* Карточки с метриками и графиками */
        .stMetric, .element-container, .stDataFrame {
            background-color: white !important;
            padding: 1.5rem !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            margin-bottom: 1rem !important;
        }
        
        /* Кнопки */
        div.stButton > button {
            background-color: white !important;
            border: 1px solid #e0e0e0 !important;
            padding: 0.5rem 1rem !important;
            border-radius: 4px !important;
            font-weight: 500 !important;
            color: #333 !important;
            width: 100% !important;
        }
        
        div.stButton > button:hover {
            background-color: #f8f9fa !important;
            border-color: #ccc !important;
        }
        
        div.stButton > button:focus {
            background-color: #ef8432 !important;
            color: white !important;
            border-color: #ef8432 !important;
        }
        
        /* Графики */
        .js-plotly-plot {
            background-color: white !important;
            border-radius: 8px !important;
            padding: 1rem !important;
        }
        
        /* Заголовки */
        h1, h2, h3 {
            color: #2e606b !important;
            font-weight: 600 !important;
        }

        /* Контейнеры с графиками */
        .chart-container {
            background-color: white !important;
            padding: 1.5rem !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            margin-bottom: 1rem !important;
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
    df['Время ответа (мин)'] = (df['Время ответа'] - df['Дата и время звонка']).dt.total_seconds() / 60
    df['Время решения (мин)'] = (df['Дата и время решения вопроса'] - df['Дата и время звонка']).dt.total_seconds() / 60
    
    return df

def filter_data_by_timerange(df, timerange):
    now = datetime.now()
    if timerange == "Сегодня":
        start_date = now - timedelta(days=1)
    elif timerange == "Неделя":
        start_date = now - timedelta(days=7)
    elif timerange == "Месяц":
        start_date = now - timedelta(days=30)
    elif timerange == "Год":
        start_date = now - timedelta(days=365)
    else:  # Все данные
        return df
    
    return df[df['Дата и время звонка'] >= start_date]

def main():
    try:
        # Загрузка данных
        df = load_data('data.json')
        
        # Заголовок и фильтры в две колонки
        header_col1, header_col2 = st.columns([0.4, 0.6])
        
        with header_col1:
            st.title("📊 Аналитика поддержки")
            st.markdown("### Анализ эффективности в реальном времени")
        
        with header_col2:
            st.markdown("### Выберите период")
            filter_cols = st.columns(5)
            
            # Initialize session state
            if 'active_timerange' not in st.session_state:
                st.session_state.active_timerange = "Все данные"
            
            # Кнопки периодов
            time_ranges = ["Сегодня", "Неделя", "Месяц", "Год", "Все данные"]
            for i, time_range in enumerate(time_ranges):
                with filter_cols[i]:
                    if st.button(
                        time_range,
                        type="primary" if st.session_state.active_timerange == time_range else "secondary"
                    ):
                        st.session_state.active_timerange = time_range
        
        # Фильтрация данных
        filtered_df = filter_data_by_timerange(df, st.session_state.active_timerange)
        
        # Расчет метрик
        metrics = {
            'avg_response_time': filtered_df['Время ответа (мин)'].mean(),
            'avg_resolution_time': filtered_df['Время решения (мин)'].mean(),
            'resolution_rate': (filtered_df['Решение вопроса'].mean() * 100),
            'avg_satisfaction': filtered_df['Оценка удовлетворённости'].mean()
        }
        
        # Отображение метрик
        st.markdown("### Ключевые показатели")
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric("Среднее время ответа", f"{metrics['avg_response_time']:.2f} мин")
        with metric_cols[1]:
            st.metric("Среднее время решения", f"{metrics['avg_resolution_time']:.2f} мин")
        with metric_cols[2]:
            st.metric("Процент решения", f"{metrics['resolution_rate']:.1f}%")
        with metric_cols[3]:
            st.metric("Средняя оценка", f"{metrics['avg_satisfaction']:.1f}/5")
        
        # Первый ряд графиков
        col1, col2 = st.columns([0.7, 0.3])
        
        with col1:
            st.markdown("### Анализ времени ответа")
            fig_response = px.bar(
                filtered_df,
                x='Услуга',
                y='Время ответа (мин)',
                color='Тема звонка',
                title="Время ответа по услугам и темам",
                color_discrete_sequence=color_palette
            )
            st.plotly_chart(fig_response, use_container_width=True)
        
        with col2:
            st.markdown("### Распределение услуг")
            fig_service = px.pie(
                filtered_df,
                names='Услуга',
                title="Распределение по услугам",
                color_discrete_sequence=color_palette
            )
            st.plotly_chart(fig_service, use_container_width=True)
        
        # Второй ряд графиков
        col3, col4 = st.columns([0.4, 0.6])
        
        with col3:
            st.markdown("### Оценки клиентов")
            fig_satisfaction = px.histogram(
                filtered_df,
                x='Оценка удовлетворённости',
                title="Распределение оценок",
                nbins=5,
                color_discrete_sequence=[color_palette[0]]
            )
            st.plotly_chart(fig_satisfaction, use_container_width=True)
        
        with col4:
            st.markdown("### Динамика времени решения")
            fig_resolution = px.line(
                filtered_df,
                x='Дата и время звонка',
                y='Время решения (мин)',
                title="Тренд времени решения",
                color_discrete_sequence=[color_palette[1]]
            )
            st.plotly_chart(fig_resolution, use_container_width=True)

        # Таблица данных
        st.markdown("### Детальные данные")
        st.dataframe(
            filtered_df[[
                'Услуга', 'Тема звонка', 'Время ответа (мин)',
                'Время решения (мин)', 'Оценка удовлетворённости', 'Решение вопроса'
            ]],
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"Ошибка при загрузке или обработке данных: {str(e)}")

if __name__ == "__main__":
    main()
