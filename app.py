import os
from threading import current_thread
import requests
import plotly.graph_objects as go

import dash
#import dash_table
from dash import dash_table
#import dash_core_components as dcc
from dash import dcc
#import dash_html_components as html
from dash import html
import dash_bootstrap_components as dbc
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

<<<<<<< HEAD
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#---------------------------------------------------------------------------
fig = go.Figure()
img_width = 920
img_height = 920
scale_factor = 0.5
fig.add_layout_image(
        x=0,
        sizex=img_width,
        y=0,
        sizey=img_height,
        xref="x",
        yref="y",
        opacity=1.0,
        layer="below",
        source="D:/sem5/python/proj/data_analysis_app/image.jpg"
)
fig.update_xaxes(showgrid=False, range=(0, img_width))
fig.update_yaxes(showgrid=False, scaleanchor='x', range=(img_height, 0))

#---------------------------------------------------------------------------
=======
#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.LUX],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )
>>>>>>> 65d674e95c7fe937912d00a488515d1126208b89
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

# TABS

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
    
app.layout = html.Div([
    dbc.Row(dbc.Col(html.H1("Activity Tracking",
                            style={"textAlign": "center"}), width=12)),
    html.Hr(),
    dbc.Row(dbc.Col(app_tabs, width=12), className="mb-3"),
    html.Div(id='content', children=[]),

    dcc.Dropdown(
        id='dropdown',
        options=[{'label': i, 'value': i} for i in id_range],
        value=current_patient + 1
    ),
    generate_table(),
    dcc.Interval(id='interval1', interval=1000, n_intervals=0),
    html.H1(id='label1', children=''),
    dcc.Graph(figure=fig)
])


@app.callback(Output('table', 'data'), Input('dropdown', 'value'))
def compute_value(value):
    current_patient = value - 1
    return dfs[current_patient].to_dict('record')

@app.callback(dash.dependencies.Output('label1', 'children'),
    [dash.dependencies.Input('interval1', 'n_intervals')])
def update_interval(n):
    return 'Intervals Passed: ' + str(n)

@app.callback(
    Output("content", "children"),
    [Input("tabs", "active_tab")]
)

def switch_tab(tab_chosen):
    if tab_chosen == "tab-main":
        return tab_chosen
    elif tab_chosen == "tab-graphs":
        return tab_chosen
    elif tab_chosen == "tab-about":
        return tab_chosen
    return html.P("This shouldn't be displayed for now...")

if __name__ == '__main__':
    app.run_server(debug=True)