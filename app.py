import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from fpdf import FPDF
import io
import base64

# Настройка страницы
st.set_page_config(
    page_title="Анализ службы поддержки",
    page_icon="📊",
    layout="wide"
)

# Цветовая палитра
COLOR_PALETTE = {
    'primary': '#FF6B6B',     # Коралловый
    'secondary': '#4ECDC4',   # Бирюзовый
    'accent1': '#45B7D1',     # Голубой
    'accent2': '#96CEB4',     # Мятный
    'accent3': '#FFEEAD',     # Пастельный желтый
}

def load_data():
    # Здесь мы создаем пример данных, в реальности здесь будет загрузка JSON
    data = {
        "Дата и время звонка": ["2024-11-30T17:01:27.859983"],
        "Тема звонка": ["Проблема с доступом"],
        "Услуга": ["Индивидуальные тренировки"],
        "Время ответа": ["2024-11-30T17:02:52.015785"],
        "Оценка удовлетворённости": [5],
        "Дата и время решения вопроса": ["2024-11-30T17:36:58.786956"],
        "Решение вопроса": [True]
    }
    df = pd.DataFrame(data)
    
    # Преобразование строковых дат в datetime
    date_columns = ["Дата и время звонка", "Время ответа", "Дата и время решения вопроса"]
    for col in date_columns:
        df[col] = pd.to_datetime(df[col])
    
    # Расчет времени ответа и решения в минутах
    df['Время до ответа (мин)'] = ((df['Время ответа'] - df['Дата и время звонка']).dt.total_seconds() / 60)
    df['Время до решения (мин)'] = ((df['Дата и время решения вопроса'] - df['Дата и время звонка']).dt.total_seconds() / 60)
    
    return df

def create_metrics(df):
    avg_response_time = df['Время до ответа (мин)'].mean()
    avg_resolution_time = df['Время до решения (мин)'].mean()
    satisfaction_rate = df['Оценка удовлетворённости'].mean()
    resolution_rate = (df['Решение вопроса'].sum() / len(df)) * 100
    
    return avg_response_time, avg_resolution_time, satisfaction_rate, resolution_rate

def create_plots(df):
    # График распределения тем обращений
    topic_fig = px.bar(
        df['Тема звонка'].value_counts().reset_index(),
        x='index',
        y='Тема звонка',
        title='Распределение тем обращений',
        color_discrete_sequence=[COLOR_PALETTE['primary']],
        labels={'index': 'Тема', 'Тема звонка': 'Количество обращений'}
    )
    
    # График распределения по услугам
    service_fig = px.bar(
        df['Услуга'].value_counts().reset_index(),
        x='index',
        y='Услуга',
        title='Распределение по услугам',
        color_discrete_sequence=[COLOR_PALETTE['secondary']],
        labels={'index': 'Услуга', 'Услуга': 'Количество обращений'}
    )
    
    # График удовлетворенности по времени
    satisfaction_fig = px.scatter(
        df,
        x='Время до решения (мин)',
        y='Оценка удовлетворённости',
        title='Зависимость удовлетворенности от времени решения',
        color_discrete_sequence=[COLOR_PALETTE['accent1']]
    )
    
    return topic_fig, service_fig, satisfaction_fig

def create_pdf_report(df, metrics):
    pdf = FPDF()
    pdf.add_page()
    
    # Заголовок
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Отчет по работе службы поддержки', 0, 1, 'C')
    pdf.ln(10)
    
    # Основные метрики
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Ключевые показатели:', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Среднее время ответа: {metrics[0]:.2f} мин', 0, 1)
    pdf.cell(0, 10, f'Среднее время решения: {metrics[1]:.2f} мин', 0, 1)
    pdf.cell(0, 10, f'Средняя оценка: {metrics[2]:.2f}', 0, 1)
    pdf.cell(0, 10, f'Процент решенных обращений: {metrics[3]:.1f}%', 0, 1)
    
    # Сохранение PDF в буфер
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer

def main():
    st.title('📊 Анализ эффективности службы поддержки')
    
    # Загрузка данных
    df = load_data()
    
    # Расчет метрик
    metrics = create_metrics(df)
    
    # Отображение основных метрик
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Среднее время ответа", f"{metrics[0]:.2f} мин")
    with col2:
        st.metric("Среднее время решения", f"{metrics[1]:.2f} мин")
    with col3:
        st.metric("Средняя оценка", f"{metrics[2]:.2f}")
    with col4:
        st.metric("Процент решения", f"{metrics[3]:.1f}%")
    
    # Создание графиков
    topic_fig, service_fig, satisfaction_fig = create_plots(df)
    
    # Отображение графиков
    st.plotly_chart(topic_fig, use_container_width=True)
    st.plotly_chart(service_fig, use_container_width=True)
    st.plotly_chart(satisfaction_fig, use_container_width=True)
    
    # Кнопка для создания PDF-отчета
    if st.button('Сгенерировать PDF-отчет'):
        pdf_buffer = create_pdf_report(df, metrics)
        b64_pdf = base64.b64encode(pdf_buffer.read()).decode()
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="support_report.pdf">Скачать PDF-отчет</a>'
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
