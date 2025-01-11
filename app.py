from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta

# Initialize Dash app
app = Dash(__name__)

# Color palette
color_palette = ['rgba(239, 132, 50, 0.7)', 'rgba(46, 96, 107, 0.7)',
                'rgba(4, 21, 35, 0.7)', 'rgba(111, 46, 24, 0.7)',
                'rgba(122, 85, 86, 0.7)', 'rgba(146, 151, 172, 0.7)']

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Аналитика поддержки</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #f0f2f6;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            }
            .dash-container {
                padding: 2rem;
                max-width: 1400px;
                margin: 0 auto;
            }
            .metric-card {
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }
            .chart-container {
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }
            h1, h2, h3 {
                color: #2e606b;
                font-weight: 600;
            }
            .time-filter button {
                background-color: white;
                border: 1px solid #e0e0e0;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-weight: 500;
                color: #333;
                margin-right: 0.5rem;
                cursor: pointer;
            }
            .time-filter button:hover {
                background-color: #f8f9fa;
                border-color: #ccc;
            }
            .time-filter button.active {
                background-color: #ef8432;
                color: white;
                border-color: #ef8432;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    df = pd.DataFrame(json_data['data'])
    
    datetime_cols = ['Дата и время звонка', 'Время ответа', 'Дата и время решения вопроса']
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])
    
    df['Время ответа (мин)'] = (df['Время ответа'] - df['Дата и время звонка']).dt.total_seconds() / 60
    df['Время решения (мин)'] = (df['Дата и время решения вопроса'] - df['Дата и время звонка']).dt.total_seconds() / 60
    
    return df

def filter_data_by_timerange(df, timerange):
    now = datetime.now()
    if timerange == "today":
        start_date = now - timedelta(days=1)
    elif timerange == "week":
        start_date = now - timedelta(days=7)
    elif timerange == "month":
        start_date = now - timedelta(days=30)
    elif timerange == "year":
        start_date = now - timedelta(days=365)
    else:  # all data
        return df
    
    return df[df['Дата и время звонка'] >= start_date]

# Load initial data
df = load_data('data.json')

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("📊 Аналитика поддержки", className="header-title"),
        html.H3("Анализ эффективности в реальном времени"),
        
        # Time range filter
        html.Div([
            html.H3("Выберите период"),
            dcc.RadioItems(
                id='time-filter',
                options=[
                    {'label': 'Сегодня', 'value': 'today'},
                    {'label': 'Неделя', 'value': 'week'},
                    {'label': 'Месяц', 'value': 'month'},
                    {'label': 'Год', 'value': 'year'},
                    {'label': 'Все данные', 'value': 'all'}
                ],
                value='all',
                className='time-filter'
            )
        ]),
    ], className="header"),
    
    # Metrics
    html.Div([
        html.Div([
            html.H3("Ключевые показатели"),
            html.Div([
                html.Div(id='avg-response-time', className='metric-card'),
                html.Div(id='avg-resolution-time', className='metric-card'),
                html.Div(id='resolution-rate', className='metric-card'),
                html.Div(id='avg-satisfaction', className='metric-card')
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '1rem'})
        ])
    ]),
    
    # Charts - First Row
    html.Div([
        html.Div([
            dcc.Graph(id='response-time-chart')
        ], className='chart-container', style={'width': '70%'}),
        html.Div([
            dcc.Graph(id='service-distribution-chart')
        ], className='chart-container', style={'width': '30%'})
    ], style={'display': 'flex', 'gap': '1rem'}),
    
    # Charts - Second Row
    html.Div([
        html.Div([
            dcc.Graph(id='satisfaction-chart')
        ], className='chart-container', style={'width': '40%'}),
        html.Div([
            dcc.Graph(id='resolution-time-trend')
        ], className='chart-container', style={'width': '60%'})
    ], style={'display': 'flex', 'gap': '1rem'}),
    
    # Data Table
    html.Div([
        html.H3("Детальные данные"),
        dash_table.DataTable(
            id='data-table',
            columns=[
                {'name': col, 'id': col} for col in [
                    'Услуга', 'Тема звонка', 'Время ответа (мин)',
                    'Время решения (мин)', 'Оценка удовлетворённости', 'Решение вопроса'
                ]
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold'
            }
        )
    ], className='chart-container')
], className='dash-container')

# Callbacks
@app.callback(
    [Output('avg-response-time', 'children'),
     Output('avg-resolution-time', 'children'),
     Output('resolution-rate', 'children'),
     Output('avg-satisfaction', 'children'),
     Output('response-time-chart', 'figure'),
     Output('service-distribution-chart', 'figure'),
     Output('satisfaction-chart', 'figure'),
     Output('resolution-time-trend', 'figure'),
     Output('data-table', 'data')],
    [Input('time-filter', 'value')]
)
def update_dashboard(timerange):
    filtered_df = filter_data_by_timerange(df, timerange)
    
    # Calculate metrics
    avg_response = filtered_df['Время ответа (мин)'].mean()
    avg_resolution = filtered_df['Время решения (мин)'].mean()
    resolution_rate = filtered_df['Решение вопроса'].mean() * 100
    avg_satisfaction = filtered_df['Оценка удовлетворённости'].mean()
    
    # Create charts
    response_time_fig = px.bar(
        filtered_df,
        x='Услуга',
        y='Время ответа (мин)',
        color='Тема звонка',
        title="Время ответа по услугам и темам",
        color_discrete_sequence=color_palette
    )
    
    service_dist_fig = px.pie(
        filtered_df,
        names='Услуга',
        title="Распределение по услугам",
        color_discrete_sequence=color_palette
    )
    
    satisfaction_fig = px.histogram(
        filtered_df,
        x='Оценка удовлетворённости',
        title="Распределение оценок",
        nbins=5,
        color_discrete_sequence=[color_palette[0]]
    )
    
    resolution_trend_fig = px.line(
        filtered_df,
        x='Дата и время звонка',
        y='Время решения (мин)',
        title="Тренд времени решения",
        color_discrete_sequence=[color_palette[1]]
    )
    
    # Format metrics
    metrics = [
        html.Div([
            html.H4("Среднее время ответа"),
            html.P(f"{avg_response:.2f} мин")
        ]),
        html.Div([
            html.H4("Среднее время решения"),
            html.P(f"{avg_resolution:.2f} мин")
        ]),
        html.Div([
            html.H4("Процент решения"),
            html.P(f"{resolution_rate:.1f}%")
        ]),
        html.Div([
            html.H4("Средняя оценка"),
            html.P(f"{avg_satisfaction:.1f}/5")
        ])
    ]
    
    # Table data
    table_data = filtered_df[[
        'Услуга', 'Тема звонка', 'Время ответа (мин)',
        'Время решения (мин)', 'Оценка удовлетворённости', 'Решение вопроса'
    ]].to_dict('records')
    
    return metrics + [
        response_time_fig,
        service_dist_fig,
        satisfaction_fig,
        resolution_trend_fig,
        table_data
    ]

if __name__ == '__main__':
    app.run_server(debug=True)
