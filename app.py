import streamlit as st
import plotly.express as px

    
def get_response_times():
    """Execute query to get response times"""
    
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
                        -- If previous message was during non-working hours (00:00-09:30)
                        WHEN TO_TIMESTAMP(rm.prev_created_at)::time < TIME '09:30:00' 
                        AND TO_TIMESTAMP(rm.created_at)::time >= TIME '09:30:00' THEN
                            EXTRACT(EPOCH FROM (
                                TO_TIMESTAMP(rm.created_at) - 
                                TO_TIMESTAMP(rm.prev_created_at)::date + INTERVAL '9 hours 30 minutes'
                            ))
                        -- If current response is after working hours
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
        print(f"Error executing query: {e}")
        return None

st.set_page_config(page_title="Manager Response Times Dashboard", layout="wide")

st.title("Manager Response Times Analysis")

# Get the data
df = get_response_times()

if df is not None:
    # Main metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Managers", len(df))
    with col2:
        st.metric("Average Response Time (min)", f"{df['avg_response_time_minutes'].mean():.2f}")
    with col3:
        st.metric("Total Responses", df['total_responses'].sum())

    # Response times bar chart
    fig1 = px.bar(
        df,
        x='name_mop',
        y='avg_response_time_minutes',
        title='Average Response Time by Manager',
        labels={'name_mop': 'Manager', 'avg_response_time_minutes': 'Average Response Time (minutes)'}
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Response count bar chart
    fig2 = px.bar(
        df,
        x='name_mop',
        y='total_responses',
        title='Total Responses by Manager',
        labels={'name_mop': 'Manager', 'total_responses': 'Total Responses'}
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Detailed data table
    st.subheader("Detailed Response Time Data")
    st.dataframe(df)
else:
    st.error("Failed to fetch data from the database. Please check your connection settings.")
    
    
