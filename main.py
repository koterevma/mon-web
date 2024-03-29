import base64
import io
import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import requests
import json
from datetime import datetime as dt, timedelta as td
from datetime import date
import db_get as db


def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                children=[
                    html.A(children=html.Img(src="assets/logo-bmstu.svg", width=60, height=60,
                                             style={'margin-bottom': '8px'}), href='https://mf.bmstu.ru/'),
                    html.Div(
                        children=[
                            html.H6("Мытищинский филиал"),
                            html.H4("МГТУ им. Н.Э.Баумана"),
                        ]
                    ),

                ], style={'display': 'flex', 'align-items': 'center'}
            ),
            html.Div(
                children=[
                    html.A(children="webrobo", href="http://webrobo.mgul.ac.ru:3000/"),
                    html.A(children="dbrobo", href="http://dbrobo.mgul.ac.ru/"),
                    html.A(children="dokuwiki", href="http://dokuwiki.mgul.ac.ru/dokuwiki/doku.php"),
                    html.A(children="Github", href='https://github.com/koterevma/mon-web')
                ]
            )
        ]
    )


def build_left_block():
    return html.Div(
        children=[
            "Прибор",
            dcc.Dropdown(id='appliances', multi=True, style={'color': 'black'}),
            "Датчик",
            dcc.Dropdown(id='sensor', multi=True, style={'color': 'black'}),
        ],
        style={'width': '65%', 'display': 'inline-block', 'padding': '10px 0px 30px 80px'}
    )


def build_centre_block():
    return html.Div(
        children=[
            "Осреднение",
            dcc.Dropdown(
                id='rounding',
                options=[
                    {'label': 'без изменений', 'value': 'none'},
                    {'label': '5 минут', 'value': '5min'},
                    {'label': 'осреднять за час', 'value': 'hour'},
                    {'label': 'осреднять за  3 часа', 'value': 'hour3'},
                    {'label': 'осреднять за  сутки', 'value': 'day'},
                    {'label': 'MAX за день', 'value': 'MAX'},
                    {'label': 'MIN за день', 'value': 'MIN'},
                ],
                value='none',
                style={'color': 'black'}
            ),

            "Тип графика",
            dcc.Dropdown(
                id='type',
                options=[
                    {'label': 'линии', 'value': 'lines'},
                    {'label': 'маркеры', 'value': 'markers'},
                    {'label': 'линии + маркеры', 'value': 'lines+markers'},
                    {'label': 'Гистограмма', 'value': 'group'}
                ],
                value='lines',
                style={'color': 'black'}
            ),
        ], style={'width': '65%', 'display': 'inline-block', 'padding': '10px 0px 0px 50px'}
    )


def build_right_block():
    return html.Div(
        children=[
            html.Div(
                [
                    "Промежуток времени",
                    dcc.DatePickerRange(
                        id='date',
                        min_date_allowed=dt(2019, 1, 28),
                        max_date_allowed=date.today() + td(days=1),
                        initial_visible_month=date.today(),
                        start_date=date.today(),
                        end_date=date.today(),
                        minimum_nights=0,
                    ),
                ],

            ),
            html.Div(
                [
                    dcc.Upload(html.Button('Загрузить JSON', className='button'), id='upload',
                               style={'padding': '20px 20px 0px 0px'}),
                    html.Div(
                        daq.BooleanSwitch(
                            id="Kalman",
                            on=True,
                            label='Фильтр',
                            color='rgb(16,119,94)',
                            labelPosition='top'
                        ),
                        # style={'display': 'inline-block'}
                    ),

                    html.Div(
                        daq.BooleanSwitch(
                            id="Online",
                            on=True,
                            label='API',
                            color='rgb(16,119,94)',
                            labelPosition='top'
                        ),
                        style={'padding': '0px 0px 0px 20px'}
                    ),

                ], style={'display': 'flex', 'align-items': 'center'},

            ),

        ], style={'width': '40%', 'display': 'inline-block', 'padding': '10px 10px 0px 50px'}
    )


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.config["suppress_callback_exceptions"] = True
app.title = 'BMSTU Grafics'
app.layout = html.Div(
    children=[
        build_banner(),
        html.Div(
            [
                build_left_block(),
                build_centre_block(),
                build_right_block(),
            ], style={'display': 'flex'}
        ),
        html.Div([dcc.Graph(id='graph',
                            config={
                                "staticPlot": False,
                                "editable": True,
                                "displayModeBar": False,
                            },
                            )], style={'width': '100%', 'padding': '0px 0px 0px 0px'})])


####################################################################
def create_dev_url(uname: str, serial: str, date_begin: dt, date_end: dt):
    url = "http://webrobo.mgul.ac.ru:3000/db_api_REST/not_calibr/log/{}%20{}/{}%20{}/{}/{}"
    return url.format(
        date_begin.strftime('%Y-%m-%d'),
        date_begin.strftime('%H:%M:%S'), 
        date_end.strftime('%Y-%m-%d'),
        date_end.strftime('%H:%M:%S'),
        uname,
        serial
    )


def create_Meteo_URL(date_begin):
    return "https://www.gismeteo.ru/diary/11441/{}/{}/".format(str(date_begin.year), str(date_begin.month), )


####################################################################
def sorting(y_temp, round_):
    if round_ == 'MAX':
        return max(y_temp)
    if round_ == 'MIN':
        return min(y_temp)
    else:
        return sum(y_temp) / len(y_temp)


####################################################################
def create_date(round_, date):
    new = dt.strptime(date, '%Y-%m-%d %H:%M:%S')
    if round_ == 'day' or round_ == 'MAX' or round_ == 'MIN':
        return dt(new.year, new.month, new.day, 0, 0, 0)
    if round_ == 'hour' or round_ == 'hour3':
        return dt(new.year, new.month, new.day, new.hour, 0, 0)
    if round_ == '5min':
        return dt(new.year, new.month, new.day, new.hour, new.minute, 0)


####################################################################
def how(date_begin, date_end, how):
    if how == "hour" or how == "day" or how == 'MAX' or how == 'MIN':
        return create_date(how, date_begin) == create_date(how, date_end)
    if how == "hour3":
        return ((create_date(how, date_end) - create_date(how, date_begin)).seconds / 3600) < 3
    if how == "5min":
        return ((create_date(how, date_end) - create_date(how, date_begin)).seconds / 60) < 5


####################################################################
def sort(round_, x_arr, y_arr):
    if round_ == "none":
        return x_arr, y_arr
    else:
        x_res, y_res = [], []

        date_begin = x_arr[0]
        y_temp = [y_arr[0]]

        for i in range(1, len(y_arr)):
            date_end = x_arr[i]

            if how(date_begin, date_end, round_):
                y_temp.append(y_arr[i])
            else:
                x_res.append((create_date(round_, date_begin).strftime('%Y-%m-%d %H:%M:%S')))
                y_res.append(sorting(y_temp, round_))
                date_begin = x_arr[i]
                y_temp = [y_arr[i]]

            if i == len(x_arr) - 1:
                x_res.append((create_date(round_, date_begin).strftime('%Y-%m-%d %H:%M:%S')))
                y_res.append(sorting(y_temp, round_))

        return x_res, y_res


####################################################################
def create_appliances_list(data):
    temp, res = {}, {}
    for item in data:
        if not "{} ({})".format(data[item]['uName'], data[item]['serial']) in temp:
            temp["{} ({})".format(data[item]['uName'], data[item]['serial'])] = create_devices(data, item)

    sorted_keys = sorted(temp, key=temp.get)
    for i in sorted_keys:
        res[i] = temp[i]

    return res


def create_appliances_list_from_db():
    temp = {}
    data = db.devices()
    for uname, serial in data:
        temp["{} ({})".format(uname.replace('%20', ' '), serial)] = [f"{uname.replace('%20', ' ')}|{serial}|{_sensor[0]}" for _sensor in db.sensors(uname, serial)]

    return dict(sorted(temp.items(), key=lambda i: i[0]))


def create_devices(data, item):
    res = []
    for i in data[item]['data']:
        try:
            float(data[item]['data'][i])
            res.append("{}|{}|{}".format(data[item]['uName'], data[item]['serial'], i))
        except ValueError:
            continue
    return res


def get_json_for_dev(uname, serial, start_date, end_date):
    full_data = {}
    dt1, dt2 = dt.fromisoformat(start_date), dt.fromisoformat(end_date)
    delta = td(hours=1)
    while dt1 <= dt2:
        print(f"Getting json log for {dt1.strftime('%Y-%m-%d %H')}")
        url = create_dev_url(uname, serial, dt1, dt1 + delta)
        try:
            f = requests.get(url)
            print("DONE")
            print(f.text)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            full_data.update(json.loads(f.text))
        dt1 += delta
    return full_data


def get_data(values_sens, start_date, end_date):
    unique_devs = {}
    for elem in values_sens:
        uname, serial, _ = elem.split('|')
        unique_devs[f"{uname}|{serial}"] = None

    for key in unique_devs.keys():
        uname, serial = key.split('|')
        unique_devs[key] = get_json_for_dev(uname, serial, start_date, end_date)
    res = {}

    for elem in values_sens:
        x_arr, y_arr = [], []
        uname, serial, sens_name = elem.split('|')
        data = unique_devs[f"{uname}|{serial}"]
        for item in data:
            try:
                y_arr.append(float(data[item]['data'][sens_name]))
                x_arr.append(data[item]['Date'])
            except ValueError:
                continue
        res[elem] = (x_arr, y_arr)

    return res


def rounding(x_arr):
    return [round(i, 3) for i in x_arr]


def parse_contests(contents, filename, date):
    temp = None
    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    if '.txt' in filename or '.json' in filename or '.JSON' in filename:
        temp = json.load(io.StringIO(decoded.decode("utf-8")))

    return temp


####################################################################
def ralman_filter(x_arr):
    sPsi = 1
    sEta = 50
    x_opt = [x_arr[0]]
    e_opt = [sEta]

    for i in range(1, len(x_arr)):
        e_opt.append((sEta ** 2 * (e_opt[-1] ** 2 + sPsi ** 2) / (sEta ** 2 + e_opt[-1] ** 2 + sPsi ** 2)) ** 0.5)
        K = e_opt[-1] ** 2 / sEta ** 2
        x_opt.append(K * x_arr[i] + (1 - K) * x_opt[i - 1])

    return x_opt


@app.callback([Output('appliances', 'options'), Output('appliances', 'value')],
              [Input('Online', 'on'),
               Input('upload', 'contents')],
              [State('upload', 'filename'), State('upload', 'last_modified')])
def update_dropdown(on, list_of_contents, list_of_names, list_of_dates):
    data = None  # Инициализировал потому что ругалась IDE
    if list_of_contents is not None and not on:
        data = parse_contests(list_of_contents, list_of_names, list_of_dates)
        # with open("log.JSON", 'r', encoding='utf-8') as read_file:
        #     data = json.load(read_file)
        return [dict(label=el, value=el) for el in create_appliances_list(data).keys()], None
    if on:
        # data = get_json(start_date, end_date)
        return [dict(label=el, value=el) for el in create_appliances_list_from_db().keys()], None


@app.callback([Output('sensor', 'options'), Output('sensor', 'value')],
              [Input('appliances', 'value')])
def update_sensor(appliances):
    res = []
    if appliances is not None:
        for i in appliances:
            lst = create_appliances_list_from_db()[i]
            for el in lst:
                res.append(dict(label=el, value=el))

    return res, None


####################################################################
@app.callback(Output('graph', 'figure'),
              [Input('sensor', 'value'), Input('date', 'start_date'), Input('date', 'end_date'),
               Input('type', 'value'),
               Input('rounding', 'value'),
               Input('Kalman', 'on')])
def update_graph(sensor, start_date, end_date, type_, round_, filter):
    fig = go.Figure()
    fig.update_layout(
        yaxis=dict(
            tickfont_size=20,
            title=''
        ),
        xaxis=dict(
            tickfont_size=20,
            title=''
        ),
        title='',
        showlegend=False,
        autosize=True,
        height=710,
        colorway=['rgb(0,48,255)', 'rgb(0,204,58)', 'rgb(255,154,0)',
                  'rgb(255,0,0)', 'rgb(180,0,210)', 'rgb(0,205,255)',
                  'rgb(115,90,79)', 'rgb(76,118,76)'],

        margin=dict(t=0, b=10, r=80, l=80),
        font_color='white',
        plot_bgcolor='white',
        paper_bgcolor="rgb(75, 75, 83)",

        hoverlabel=dict(
            bgcolor="rgb(75, 75, 83)",
            font_size=16,
            font_family="Rockwell",
        ),
        hovermode="x unified"

    )
    fig.update_xaxes(
        linecolor='Gainsboro',
        gridcolor='Gainsboro',
        zerolinecolor='Gainsboro',
        # rangeslider_visible=True,
        # rangeselector=dict(
        #     buttons=list([
        #         dict(count=1, label="1H", step="hour", stepmode="backward"),
        #         dict(count=3, label="3H", step="hour", stepmode="backward"),
        #         dict(count=1, label="1D", step="day", stepmode="todate"),
        #         dict(step="all")
        #     ])
        # )
    ),
    fig.update_yaxes(

        linecolor='Gainsboro',
        gridcolor='Gainsboro',
        zerolinecolor='Gainsboro',
    )

    if sensor is None:
        return fig

    if sensor != []:
        """Надо сделать нормальное отображение едениц измерения - например degC - это
        degree Celsius то есть градусы цельсия"""
        fig.update_layout(yaxis=dict(title=db.units(sensor[0].split('|')[2])[0], titlefont_size=22))

    data = get_data(sensor, start_date, end_date)

    for key, value in data.items():
        uname, serial, sens_name = key.split('|')
        x_arr, y_arr = value
        x_arr, y_arr = sort(round_, x_arr, y_arr)

        if filter:
            y_arr = ralman_filter(y_arr)

        y_arr = rounding(y_arr)

        if 'group' in type_:
            fig.add_trace(go.Histogram(x=x_arr, y=y_arr, name="{} ({})".format(uname + ' ' + serial, sens_name)))
            fig.update_traces(opacity=0.4)
            # fig.update_traces(opacity=0.4, histnorm="density", histfunc="sum")
            fig.update_layout(barmode='overlay')
        else:
            fig.add_trace(go.Scatter(x=x_arr, y=y_arr, mode=type_,
                                     name="{} ({})".format(uname + ' ' + serial, sens_name),
                                     hovertemplate="<b>%{y}</b>"))

    return fig


server = app.server  # Для деплоя


if __name__ == '__main__':
    app.run_server(debug=True)  # True если надо получать сообщения об ошибках
