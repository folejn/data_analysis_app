import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from dash import html
import dash_bootstrap_components as dbc

import dash
from dash import html
from dash import dcc
from dash import dash_table
import numpy as np
from dash.dependencies import Input, Output, State

from my_queue_queries import get_current_patient_data, get_patient_values, get_sensors_values, if_set_alarm, update_table_patient_data
import figure_styling
import url_services.repository
from url_services.url_service import UrlService
from url_services.repository import q1

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
    print(f'Computing for patient: {current_patient}')
    return dash_table.DataTable(
        id='table', data=dataframe.to_dict('records'),
        columns=[{"name": i, "id": i} for i in dataframe.columns],
        style_data={
            'color': 'black',
            'backgroundColor': 'white'
        },
    )
    
def generate_anomalies_table(current_patient, max_rows=40): #dataframe
    df = url_services.repository.get_anomalies(current_patient)
    dataframe = df
    return dash_table.DataTable(
        id='anomalies_table', data=dataframe.to_dict('records'),
        columns=[{'id': "datetime", 'name': "datetime"}, {'id': "anomaly", 'name': "anomaly"},
                 {'id': "value", 'name': "value"}, {'id': "name", 'name': "sensor"}],
        page_current=0,
        page_size=6,
        page_action='custom'
    )

def generate_fig(current_patient, df):
    fig = go.Figure()

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
        cmin=0, cmax=1300
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
    generate_table(current_patient=5),
    dcc.Interval(id='interval1', interval=1000, n_intervals=0),
    html.H1(id='label1', children=''),
    html.Div(dcc.Graph( id="main_graph",
        ), style={
            "width": "100%",
            "display": "flex",
            "justify-content": "center",
    }),
    'Anomalies history:',
    generate_anomalies_table(current_patient=5),
])

tab_graphs = html.Div([
    dcc.Interval(id='interval2', interval=5*1000, n_intervals=0),
    html.Div(dcc.Graph(id="trace_graph")),
])

app.layout = html.Div([
    dbc.Row(dbc.Col(html.H1("Activity Tracking",
                            style={"textAlign": "center"}), width=12)),
    html.Hr(),
    dcc.Dropdown(
        id='dropdown',
        options=[{'label': i, 'value': i} for i in id_range],
        value=5
    ),
    dbc.Row(dbc.Col(app_tabs, width=12), className="mb-3"),
    html.Div(id='content', children=[]),

])
@app.callback([Output('table', 'data'), Output('main_graph','figure'), Output('table', 'style_data')], #
              [Input('dropdown', 'value'), Input('interval1', 'n_intervals')])
def real_time_data(value, n):
    df = url_services.repository.get_latest()
    current_patient = value
    job = q1.enqueue(update_table_patient_data, args = (df, current_patient))
    while job.result is None:
        pass
    result = job.result
    
    alarm = len(result[result["anomaly"] == "True"]) > 0
    if alarm:
        style_data={
            'color': 'white',
            'backgroundColor': 'red'
        }
    else: 
        style_data={
            'color': 'black',
            'backgroundColor': 'white'
        }

    figure = generate_fig(current_patient=current_patient, df=result)    
    return result.to_dict('record'), figure,style_data

@app.callback(Output('anomalies_table', 'data'), 
              [Input('interval1', 'n_intervals'), 
              Input('dropdown', 'value'), 
              Input('anomalies_table', "page_current"),
            Input('anomalies_table', "page_size")])
def update_anomalies(n, current_patient, page_current, page_size):
    anomalies_df = url_services.repository.get_anomalies(current_patient)
    if not anomalies_df.empty:
        return anomalies_df.iloc[page_current*page_size:(page_current+ 1)*page_size].to_dict('records')
    pass

@app.callback(Output('trace_graph', 'figure'), [Input('interval2', 'n_intervals'), Input('dropdown', 'value')])
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
        return tab_graphs
    elif tab_chosen == "tab-about":
        return tab_chosen
    return html.P("This shouldn't be displayed for now...")

if __name__ == '__main__':
    service = UrlService("Request for data")
    service.setDaemon(True)
    service.start()
    app.run_server(debug=True)