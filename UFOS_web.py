import json
import os
import re

import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, callback


def get_ufos_folders(path="."):
    digital_list = sorted([int(i.split('_')[-1]) for i in os.listdir(path) if re.match(r"Ufos_\d*", i)], reverse=True)
    return [f"Ufos_{i}" for i in digital_list]


def get_ufos_default(path="common_settings.json"):
    with open(path) as fr:
        return f'Ufos_{json.load(fr)["device"]["id"]}'


@callback(
    [Output('local-storage', 'data'),
     Output('ufos-dropdown', 'value'),
     Output('year-dropdown', 'value'),
     Output('month-dropdown', 'value'),
     Output('day-dropdown', 'value')],
    [Input('local-storage', 'data'),
     Input('ufos-dropdown', 'value'),
     Input('year-dropdown', 'value'),
     Input('month-dropdown', 'value'),
     Input('day-dropdown', 'value')])
def save_data(data, ufos, year, month, day):
    ufos = ufos or str(data.get('ufos'))
    data['ufos'] = ufos
    path = [ufos, 'Mesurements']

    year = year or str(data.get('year'))
    path.append(year)
    data['year'] = year if os.path.exists(os.path.join(*path)) else None

    month = month or str(data.get('month'))
    path.append(month)
    data['month'] = month if os.path.exists(os.path.join(*path)) else None

    day = day or str(data.get('day'))
    path.append(day)
    data['day'] = day if os.path.exists(os.path.join(*path)) else None
    return data, data['ufos'], data['year'], data['month'], data['day']


@callback(
    Output('year-dropdown', 'options'),
    Input('local-storage', 'data'))
def get_year_folders(data):
    return [i for i in sorted(os.listdir(os.path.join(data['ufos'], 'Mesurements')), reverse=True)
            if re.fullmatch(r"\d\d\d\d", str(i))]


@callback(
    Output('month-dropdown', 'options'),
    Input('local-storage', 'data'))
def get_month_folders(data):
    path = [os.path.abspath(data['ufos']), 'Mesurements', data['year']]
    if all(path):
        return [i for i in sorted(os.listdir(os.path.join(*path)), reverse=True)
                if re.fullmatch(r"\d\d\d\d-\d\d", str(i))]
    else:
        return []


@callback(
    Output('day-dropdown', 'options'),
    Input('local-storage', 'data'))
def get_day_folders(data):
    path = [os.path.abspath(data['ufos']), 'Mesurements', data['year'], data['month']]
    if all(path):
        return [i for i in sorted(os.listdir(os.path.join(*path)), reverse=True)
                if re.fullmatch(r"\d\d\d\d-\d\d-\d\d", str(i))]
    else:
        return []


@callback(
    [Output('file-list', 'options'),
     Output('file-list-storage', 'data')],
    Input('local-storage', 'data'),
    prevent_initial_call=True)
def get_files_list(data):
    path = [os.path.abspath(data['ufos']), 'Mesurements', data['year'], data['month'], data['day']]
    if all(path):
        day_folder = os.path.join(*path)
        files = {i: os.path.join(day_folder, i) for i in sorted(os.listdir(day_folder), reverse=True)}
        return list(files), files
    else:
        return [], {}


@callback(
    Output('file-graph', 'figure'),
    [Input('file-list', 'value'),
     Input('file-list-storage', 'data')],
    prevent_initial_call=True)
def draw_files(selected_names, files_dict):
    all_graphs = []
    if not selected_names:
        return graph_default
    for name in selected_names:
        path = files_dict.get(name)
        with open(path) as fr:
            spectr = json.load(fr)["spectr"]
            graph = go.Scatter(x=list(range(len(spectr))), y=spectr, name=name)
            all_graphs.append(graph)
    return go.Figure(data=all_graphs, layout={'margin': {i: 0 for i in 'blrt'}, 'legend': {'y': 0.9}})


app = Dash(__name__, external_stylesheets=['style.css'])
# app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

graph_default = go.Figure(data=[go.Scatter(x=[], y=[])],
                          layout={'margin': {i: 0 for i in 'blrt'}})

app.layout = html.Div(children=[
    dcc.Store(id='local-storage', storage_type='local'),
    dcc.Store(id='file-list-storage', storage_type='session'),
    html.Table(style={"width": "99%", "align": "center", "border": 1}, children=[
        html.Tr([
            html.Td(colSpan=5, children=[
                html.H1(style={"text-align": "center"}, children="Ultraviolet Ozone Spectrometer (UFOS)")
            ]),
        ]),
        # ===== Row 1 =====
        html.Tr([
            html.Td(style={"width": "70px", "height": "35px", "white-space": "nowrap"}, children=[
                html.P(children="UFOS №"),
            ]),
            html.Td(style={"width": "120px"}, children=[
                dcc.Dropdown(get_ufos_folders(), None, id='ufos-dropdown'),
            ]),
            html.Td(rowSpan=5, children=[
                dcc.Graph(id='file-graph')
            ]),
        ]),
        # ===== Row 2 =====
        html.Tr([
            html.Td(style={"height": "35px", "white-space": "nowrap"}, children=[
                html.P(children="Год"),
            ]),
            html.Td(children=[
                dcc.Dropdown([], None, id='year-dropdown'),
            ]),
        ]),
        # ===== Row 3 =====
        html.Tr([
            html.Td(style={"height": "35px", "white-space": "nowrap"}, children=[
                html.P(children="Месяц"),
            ]),
            html.Td(children=[
                dcc.Dropdown([], None, id='month-dropdown'),
            ]),
        ]),
        # ===== Row 4 =====
        html.Tr([
            html.Td(style={"height": "35px", "white-space": "nowrap"}, children=[
                html.P(children="День"),
            ]),
            html.Td(children=[
                dcc.Dropdown([], None, id='day-dropdown'),
            ]),
        ]),
        # ===== Row 5 =====
        html.Tr([
            html.Td(colSpan=2, style={"vertical-align": "top"}, children=[
                dcc.Dropdown(id='file-list', options=[], multi=True, style={"width": "300px"})
            ]),
        ]),
    ]),
])

if __name__ == "__main__":
    app.run_server(debug=True)
