import os
from time import sleep
from pandas.core.frame import DataFrame
import requests
import plotly.graph_objects as go

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
from my_queue_queries import get_current_patient_data, get_patient_values, update_table_patient_data
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

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.LUX],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
#to be moved to another file
#--------------------------------------
id_range = range(1, 7)
patients_names = {}
#N = 100
def get_data():
    for _id in id_range:
        patient = requests.get(url=f"http://tesla.iem.pw.edu.pl:9080/v2/monitor/{_id}")
        json_inf = patient.json()
        patients_names[_id] = f"{json_inf['firstname']} {json_inf['lastname']}; disability: {json_inf['disabled']} "
    return get_sensors_data()
        
def get_sensors_data():
    sensors_dict = {}
    for p_id in id_range:
        if p_id not in sensors_dict.keys():
            sensors_dict[p_id] = []
        patient = requests.get(url=f"http://tesla.iem.pw.edu.pl:9080/v2/monitor/{p_id}")
        patient_json = patient.json()
        for measurment in patient_json["trace"]["sensors"]:
            measurment['anomaly'] = str(measurment['anomaly'])
            sensors_dict[p_id].append(measurment)
            #print(measurment)
    return sensors_dict
#------------------------------------------------------------------------------
current_patient = 5
dfs = [pd.DataFrame(get_data()[i]) for i in id_range]
for i in id_range:
    dfs[i-1]["patient_id"] = i
df = pd.concat(dfs)
print(df)

    
def generate_table( max_rows=40): #dataframe
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
        value=current_patient
    ),
    generate_table(),
    dcc.Interval(id='interval1', interval=1000, n_intervals=0),
    html.H1(id='label1', children=''),
    html.Div(dcc.Graph( id="main_graph",
        ), style={
            "width": "100%",
            "display": "flex",
            "justify-content": "center",
    }),
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