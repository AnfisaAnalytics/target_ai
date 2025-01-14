import streamlit as st
import plotly.express as px
import psycopg2
import pandas as pd

def connect_to_db():
    try:
        conn = psycopg2.connect(
            host="rc1a-p8bp15mmxsfwpbt0.mdb.yandexcloud.net",
            port="6432",
            database="db1",
            user="test_user",
            password="j2M{CnnFq@"
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None
    
def get_response_times():
    """Выполнить запрос для получения времени ответа"""
    query = """
    WITH ranked_messages AS (
        SELECT 
            m.message_id,
            m.type,
            m.entity_id,
            m.created_by,
            m.created_at,
            mg.name_mop,
            LAG(m.type) OVER (PARTITION BY m.entity_id ORDER BY m.created_at) as prev_type,
            LAG(m.created_at) OVER (PARTITION BY m.entity_id ORDER BY m.created_at) as prev_created_at
        FROM test.chat_messages m
        LEFT JOIN test.managers mg ON m.created_by = mg.mop_id
        ORDER BY m.entity_id, m.created_at
    ),
    response_times AS (
        SELECT 
            rm.*,
            CASE 
                WHEN rm.type = 'outgoing_chat_message' 
                AND rm.prev_type = 'incoming_chat_message' THEN
                    CASE 
                        -- Если предыдущее сообщение было в нерабочее время (00:00-09:30)
                        WHEN TO_TIMESTAMP(rm.prev_created_at)::time < TIME '09:30:00' 
                        AND TO_TIMESTAMP(rm.created_at)::time >= TIME '09:30:00' THEN
                            EXTRACT(EPOCH FROM (
                                TO_TIMESTAMP(rm.created_at) - 
                                TO_TIMESTAMP(rm.prev_created_at)::date + INTERVAL '9 hours 30 minutes'
                            ))
                        -- Если текущий ответ после рабочего времени
                        WHEN TO_TIMESTAMP(rm.created_at)::time > TIME '00:00:00' THEN
                            EXTRACT(EPOCH FROM (
                                TO_TIMESTAMP(rm.created_at) - 
                                TO_TIMESTAMP(rm.prev_created_at)
                            ))
                        ELSE NULL
                    END
                ELSE NULL
            END as response_time_seconds
        FROM ranked_messages rm
    )
    SELECT 
        name_mop,
        COUNT(*) as total_responses,
        ROUND(AVG(response_time_seconds)/60, 2) as avg_response_time_minutes,
        ROUND(MIN(response_time_seconds)/60, 2) as min_response_time_minutes,
        ROUND(MAX(response_time_seconds)/60, 2) as max_response_time_minutes
    FROM response_times
    WHERE response_time_seconds IS NOT NULL
    AND name_mop IS NOT NULL
    GROUP BY name_mop
    ORDER BY avg_response_time_minutes;
    """
    
    try:
        conn = connect_to_db()
        if conn:
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        return None
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        return None

st.set_page_config(page_title="Анализ времени ответа менеджеров", layout="wide")

st.title("Анализ времени ответа службы поддержки")

# Получение данных
df = get_response_times()

if df is not None:
    # Основные метрики
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего менеджеров", len(df))
    with col2:
        st.metric("Среднее время ответа (мин)", f"{df['avg_response_time_minutes'].mean():.2f}")
    with col3:
        st.metric("Всего обращений", df['total_responses'].sum())

    # График среднего времени ответа
    fig1 = px.bar(
        df,
        x='name_mop',
        y='avg_response_time_minutes',
        title='Среднее время ответа по менеджерам',
        labels={
            'name_mop': 'Менеджер', 
            'avg_response_time_minutes': 'Среднее время ответа (минуты)'
        }
    )
    st.plotly_chart(fig1, use_container_width=True)

    # График количества ответов
    fig2 = px.bar(
        df,
        x='name_mop',
        y='total_responses',
        title='Количество обработанных обращений по менеджерам',
        labels={
            'name_mop': 'Менеджер', 
            'total_responses': 'Количество обращений'
        }
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Детальная таблица данных
    st.subheader("Детальная статистика по менеджерам")
    st.dataframe(df.rename(columns={
        'name_mop': 'Менеджер',
        'total_responses': 'Всего обращений',
        'avg_response_time_minutes': 'Среднее время ответа (мин)',
        'min_response_time_minutes': 'Минимальное время ответа (мин)',
        'max_response_time_minutes': 'Максимальное время ответа (мин)'
    }))
