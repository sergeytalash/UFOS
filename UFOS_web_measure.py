import os
import time
from datetime import datetime

import plotly.graph_objs as go
import serial
from dash import Dash, dcc, html, Input, Output, callback


class SetUpCOM:
    def __init__(self, to=None):
        self.opened_serial = None
        self.br = 115200  # Baudrate
        self.to = to  # Time out (s)

    def _call_serial(self, port):
        self.opened_serial = serial.Serial(
            port=port,
            baudrate=self.br,
            timeout=self.to)
        self.opened_serial.close()
        return {'com_number': os.path.split(port)[-1], 'com_obj': self.opened_serial}

    def get_com(self):
        if os.name != 'posix':
            import winreg
            registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "HARDWARE\\DEVICEMAP\\SERIALCOMM")
            for i in range(255):
                try:
                    name, value, typ = winreg.EnumValue(registry_key, i)
                    if 'USBSE' in name or 'VSerial9_0' in name:
                        return self._call_serial(port=f'//./{value}')
                except:
                    pass
        else:
            for device in os.listdir('/dev'):
                if f'tty.usbmodem' in device:
                    try:
                        return self._call_serial(port=f'/dev/tty.{device}')
                    except:
                        pass
        return {'com_number': None, 'com_obj': None}


class UfosDataToCom:
    def __init__(self, expo, mesure_type, start=b'S'):
        self.expo = expo
        self.data_send = (
                b'#\x00\x01' +
                bytes((int(expo) % 256, int(expo) // 256)) +
                b'0' +
                b'1' +
                b'0' +
                mesure_type +  # Z, S, D
                start +  # S
                b'0')

    def device_ask(self):
        com_data = b''
        request_bytes = 1000
        expo = self.expo // 1000 + 1
        t = datetime.now()
        com_obj = SetUpCOM(to=1).get_com()['com_obj']
        print(f"SetUpCOM {2}", datetime.now() - t)
        t = datetime.now()

        com_obj.open()

        com_obj.write(self.data_send)

        t = datetime.now()
        time.sleep(expo)
        print(f"sleep {expo}", datetime.now() - t)

        t = datetime.now()
        byte = com_obj.read(1000)
        print(f"com_obj.read({1000})", datetime.now() - t)
        while byte:
            com_data += byte
            if len(byte) < request_bytes:
                break
            else:
                t = datetime.now()
                byte = com_obj.read(request_bytes)
                print(f"com_obj.read({request_bytes})", datetime.now() - t)

        # print("com_obj.read all", datetime.now() - t)

        # byte = com_obj.read(1000)
        # print(f"End lost data: {byte}")
        com_obj.close()
        return com_data

    def device_ask_waiting(self):
        com_data = b''
        expo = self.expo // 1000 + 1
        t = datetime.now()
        com_obj = SetUpCOM().get_com()['com_obj']
        print(f"COM Timeout: None", datetime.now() - t)
        com_obj.open()
        com_obj.write(self.data_send)

        t = datetime.now()
        time.sleep(expo)
        print(f"sleep {expo}", datetime.now() - t)

        t = datetime.now()

        while com_obj.in_waiting() > 0:
            com_data += com_obj.read(com_obj.in_waiting())

        print(f"com_obj.read all", datetime.now() - t)

        com_obj.close()
        return com_data

    def get_spectre(self, com_data):
        if len(com_data) > 13:  # 7381:
            start = 0
            i = len(com_data) - 1
            spectr = []
            while i > start:
                i -= 1
                try:
                    d = int(com_data[i + 1]) * 255 + int(com_data[i])
                    if d > 55000:
                        d = -10
                    spectr.append(d)
                except:
                    spectr.append(2000)
                i -= 1
            return spectr[:3620]
        return [-10] * 20


@callback(
    Output('slider-output-container', 'children'),
    Input('expo-slider', 'value'))
def update_slider(expo):
    return f'Exposition: {expo}'


@callback(
    Output('com-connect-container', 'children'),
    Input('com-connect', 'n_clicks'),
    prevent_initial_call=True)
def com_connect_button(n_clicks):
    try:
        text = SetUpCOM(to=1).get_com()['com_number']
    except Exception as err:
        print(err)
        text = "Device not found"
    return f"COM: {text}"


@callback(
    [Output('graph', 'figure'),
     Output('com-data-container', 'children')],
    [Input('start', 'n_clicks'),
     Input('expo-slider', 'value'),
     Input('channel', 'value'),
     Input('graph-slider', 'value')],
    prevent_initial_call=True)
def start(n_clicks, expo, channel, interval):
    global spectr
    global com_lock
    global counter
    print(counter)
    counter += 1
    com_data = b''
    if not com_lock:
        com_lock = True
        dcom = UfosDataToCom(50, channel.encode(), b'N')
        com_data = dcom.device_ask_waiting()
        print(f"Len: {len(com_data)}, {com_data}")
        dcom = UfosDataToCom(expo, channel.encode())
        com_data = dcom.device_ask_waiting()
        print(f"Len: {len(com_data)}, {com_data}")
        com_lock = False
        start = interval[0]
        end = interval[1]
        spectr = dcom.get_spectre(com_data)[start:end]
    return (
        go.Figure(data=[go.Scatter(x=list(range(len(spectr))), y=spectr)]),
        f"[{datetime.now()}] com_data: {len(com_data)}")


@callback(
    Output('graph-slider-output-container', 'children'),
    Input('graph-slider', 'value'))
def update_slider(interval):
    go.Figure(data=[go.Scatter(x=list(range(interval[0], interval[1])), y=spectr)])
    return f'Interval: {interval}'


com_lock = False
external_stylesheets = ['style.css']
ufos_com = ''
spectr = [-1] * 10
app = Dash(__name__, external_stylesheets=external_stylesheets)
counter = 0
data = {"Pixels": [1, 2, 3], "Values": [1, 3, 2]}
app.layout = html.Div([
    html.Br(),
    dcc.Slider(100, 4000, value=100, id='expo-slider'),
    html.Div(id='slider-output-container'),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # in milliseconds
        n_intervals=0
    ),
    html.Br(),

    html.Button('Connect', id='com-connect', n_clicks=0),
    html.Div(id='com-connect-container'),
    html.Br(),

    html.Button('Start', id='start', n_clicks=0),
    html.Br(),
    dcc.RadioItems(['Z', 'S', 'D'], 'Z', id='channel', inline=True),
    html.Div(id='com-data-container'),
    dcc.Graph(
        id='graph',
        figure={
            "data": [
                {
                    "x": data["Pixels"],
                    "y": data["Values"],
                    "type": "lines",
                },
            ],
            "layout": {"title": "file"},
        },
    ),
    dcc.RangeSlider(0, 3691, value=[0, 3691], id='graph-slider'),
    html.Div(id='graph-slider-output-container')
])

if __name__ == "__main__":
    app.run_server(debug=True)
