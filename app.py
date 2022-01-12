import os
import copy
from threading import current_thread
import time
import datetime
import json
import requests
from pandas.io.json import json_normalize

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output
from requests.sessions import Request
from werkzeug.wrappers import response
from flask_caching import Cache


external_stylesheets = [
    # Dash CSS
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    # Loading screen CSS
    'https://codepen.io/chriddyp/pen/brPBPO.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
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

current_patient = 5
#df = pd.DataFrame(get_data()[current_patient])
dfs = [pd.DataFrame(get_data()[i]) for i in id_range]
len(dfs)
def generate_table( max_rows=40): #dataframe
    dataframe = dfs[current_patient]
    print(f'Computing for patient: {current_patient}')
    print(dataframe)
    print(dataframe.to_dict('records'))
    return dash_table.DataTable(
        id='table', data=dataframe.to_dict('records'),
        columns=[{"name": i, "id": i} for i in dataframe.columns],
    )
    
app.layout = html.Div([
    dcc.Dropdown(
        id='dropdown',
        options=[{'label': i, 'value': i} for i in id_range],
        value=current_patient + 1
    ),
    generate_table(),
    dcc.Interval(id='interval1', interval=1000, n_intervals=0),
    html.H1(id='label1', children=''),

])


@app.callback(Output('table', 'data'), Input('dropdown', 'value'))
def compute_value(value):
    current_patient = value - 1
    return dfs[current_patient].to_dict('record')

@app.callback(dash.dependencies.Output('label1', 'children'),
    [dash.dependencies.Input('interval1', 'n_intervals')])
def update_interval(n):
    return 'Intervals Passed: ' + str(n)

if __name__ == '__main__':
    app.run_server(debug=True)