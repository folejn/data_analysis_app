import os
from time import sleep
import random
from pandas.core.frame import DataFrame
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash import html
import dash_bootstrap_components as dbc

import dash
#import dash_table
#import dash_core_components as dcc
#import dash_html_components as html
from dash import html
from dash import dcc
from dash import dash_table
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output, State
from requests.sessions import Request
from werkzeug.wrappers import response
from flask_caching import Cache

from rq import Queue
from redis import Redis
from my_queue_queries import get_current_patient_data, get_patient_values, get_sensors_values, update_table_patient_data
import figure_styling
import url_services.repository
from url_services.url_service import UrlService

conn1 = Redis('127.0.0.1', 6379)

q1 = Queue('low', connection=conn1, job_timeout='3m')
external_stylesheets = [
    # Dash CSS
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    # Loading screen CSS
    'https://codepen.io/chriddyp/pen/brPBPO.css']

#---------------------------------------------------------------------------
id_range = range(1,7)
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.LUX],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
    
def generate_table(current_patient=5, max_rows=40): #dataframe
    df = url_services.repository.get_latest()
    job = q1.enqueue(get_current_patient_data, args = (df, current_patient))
    while job.result is None:
        pass
    dataframe = job.result
    #dataframe = df[df["patient_id"] == current_patient].drop('patient_id', axis=1)
    print(f'Computing for patient: {current_patient}')
    print(dataframe)
    print(dataframe.to_dict('records'))
    return dash_table.DataTable(
        id='table', data=dataframe.to_dict('records'),
        columns=[{"name": i, "id": i} for i in dataframe.columns],
    )

def generate_fig(current_patient, df):
    fig = go.Figure()
    color = ['rgb(93, 164, 214)', 'rgb(255, 144, 14)', 'rgb(44, 160, 101)','rgb(93, 164, 214)', 'rgb(255, 144, 14)', 'rgb(44, 160, 101)']

    #foot_values = df[df['patient_id'] == current_patient]['value'].values.tolist()
    job = q1.enqueue(get_patient_values, args = (df, current_patient))
    
    while job.result is None:
        pass
    foot_values = job.result.values.tolist()
    
    figure_styling.style(fig)
    fig.add_trace(go.Scatter(x=[120,50,100, 280, 350, 300], y=[120,200,450, 120, 200, 450], mode='markers+text',text=foot_values, marker=dict(
        color=(foot_values+[100,0]),
        size=30,
        showscale=True,
        colorscale='temps',
    )))
    return fig

def sensors_history_fig(current_patient, df):
    sensors = ["L0", "L1", "L2", "R0", "R1", "R2"]
    fig = make_subplots(rows=3, cols=2, shared_xaxes=True, shared_yaxes=True,
                        row_titles=["0", "1", "2"], column_titles=["L", "R"])
    job = q1.enqueue(get_current_patient_data, args = (df, current_patient))
    while job.result is None:
        pass
    res = job.result
    
    sensors_with_axes_coor = zip(sensors, [(1,1), (2,1), (3,1), (1,2), (2,2), (3,2)])
    for sensor in sensors_with_axes_coor:
        sensor_type, (row, col) = sensor
        job = q1.enqueue(get_sensors_values, args = (res, sensor_type, 10))
        while job.result is None:
            pass
        sensor_values = job.result
        t = np.linspace(0, 10, num = len(sensor_values))
        fig.add_trace(go.Scatter(x=t, y=sensor_values.iloc[::-1], name=sensor_type), row=row, col=col)
    fig.update_yaxes(range = [0,1300])
    return fig

app_tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(label="Main page", tab_id="tab-main", labelClassName="text-success font-weight-bold", activeLabelClassName="text-danger"),
                dbc.Tab(label="Statistical graphs", tab_id="tab-graphs", labelClassName="text-success font-weight-bold", activeLabelClassName="text-danger"),
                dbc.Tab(label="About", tab_id="tab-about", labelClassName="text-success font-weight-bold", activeLabelClassName="text-danger"),
            ],
            id="tabs",
            active_tab="tab-main",
        ),
    ], className="mt-3"
)

main_layout = html.Div([
    dcc.Dropdown(
        id='dropdown',
        options=[{'label': i, 'value': i} for i in id_range],
        value=5
    ),
    generate_table(current_patient=5),
    dcc.Interval(id='interval1', interval=1000, n_intervals=0),
    dcc.Interval(id='interval2', interval=5*1000, n_intervals=0),
    html.H1(id='label1', children=''),
    html.Div(dcc.Graph( id="main_graph",
        ), style={
            "width": "100%",
            "display": "flex",
            "justify-content": "center",
    }),
    html.Div(dcc.Graph(id="trace_graph")),
])
app.layout = html.Div([
    dbc.Row(dbc.Col(html.H1("Activity Tracking",
                            style={"textAlign": "center"}), width=12)),
    html.Hr(),
    dbc.Row(dbc.Col(app_tabs, width=12), className="mb-3"),
    html.Div(id='content', children=[]),

])
@app.callback([Output('table', 'data'), Output('main_graph','figure')],
              [Input('dropdown', 'value'), Input('interval1', 'n_intervals')])
def compute_value(value, n):
    df = url_services.repository.get_latest()
    current_patient = value
    job = q1.enqueue(update_table_patient_data, args = (df, current_patient))
    while job.result is None:
        pass
    result = job.result
    
    figure = generate_fig(current_patient=current_patient, df=df)
    
    return result.to_dict('record'), figure

@app.callback(Output('trace_graph', 'figure'), Input('interval2', 'n_intervals'), State('dropdown', 'value'))
def serve_graphs(n, current_patient):
    whole_df = url_services.repository.get_all()
    trace_figure = sensors_history_fig(current_patient=current_patient, df=whole_df)
    return trace_figure


@app.callback(
    Output("content", "children"),
    [Input("tabs", "active_tab")]
)

def switch_tab(tab_chosen):
    if tab_chosen == "tab-main":
        return main_layout
    elif tab_chosen == "tab-graphs":
        return tab_chosen
    elif tab_chosen == "tab-about":
        return tab_chosen
    return html.P("This shouldn't be displayed for now...")

if __name__ == '__main__':
    service = UrlService("Request for data")
    service.start()
    app.run_server(debug=True)