import io
import json
import urllib
import base64
from decimal import Decimal
import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

### import functions from directories ###
from ineq_app import app
from utils import(
    navigation2,
    top_banner,
    path2file,
    encode_svg,
    labels_dict,
    RF_orange,
    RF_gray,
    download_dropdown,
    button_help,
)

### load in data ###
with open(path2file('kommuner4.geojson')) as geo:
    geojson = json.load(geo)
with open(path2file('kommune_koder.json'), encoding='utf-8') as komk:
    komkoder  = json.load(komk)
komkoder2str = {int(k): str(v) for k, v in komkoder.items()}
komstr2koder = {str(v): int(k) for k, v in komkoder.items()}

# pd.options.display.float_format = '{:.3f}'.format
df = pd.read_csv(path2file('health.csv'))
df = df.astype({'KOMKODE':'int', 'year':'int'}) # ensure correct type
df = df.sort_values(by=['year', 'KOMKODE'])

health_icon = encode_svg('health_dark.svg')
health_icon_active = encode_svg('health_orange.svg')

# create dict for unique ages in health. Not the smoothest solution, consider changing
health_age_dict = {
'age1': '18 og 29',
'age2': '30 og 39',
'age3': '40 og 49',
'age4': '50 og 59',
'age5': '60 år og derover',
}

controls = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Label(['Sundhedsmål:', button_help('health', '0')]),
            dbc.Select(
               id='health-variable-selector',
               options=[
                    {'label': labels_dict['admissions'], 'value': 'admissions'},
                    {'label': labels_dict['nights'], 'value': 'nights'},
                    {'label': labels_dict['gp'], 'value': 'gp'},
                    {'label': 'Afstand til  nærmeste læge', 'value':None, 'disabled':True},
                    {'label': labels_dict['copd'], 'value': 'copd', 'disabled':True},
                    {'label': labels_dict['t2diabetes'], 'value': 't2diabetes', 'disabled':True}
               ],
               value='admissions',
            ),
            dbc.Label(['Målt ved:', button_help('health', '1')]),
            dbc.Select(
               id='health-measure-selector',
               value='Gini',
            ),
        ], width=3),
    	dbc.Col([
            dbc.Label(['Køn:', button_help('health', '2')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Kvinder", "value": 'woman'},
                    {"label": "Mænd", "value": 'man'},
                ],
                value='all',
                id="health-gender-selector",
            ),
        ], width=1),
        dbc.Col([
            dbc.Label(['Alder:',  button_help('health', '6')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "18-29 år", "value": 'age1'},
                    {"label": "30-39 år", "value": 'age2'},
                    {"label": "40-49 år", "value": 'age3'},
                    {"label": "50-59 år", "value": 'age4'},
                    {"label": "60 år og derover", "value": 'age5'},
                ],
                value='all',
                id="health-age-selector",
            ),
        ], width=1),
        dbc.Col([
            dbc.Label(['Herkomst:', button_help('health', '3')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Dansk", "value": 'danish'},
                    {"label": "Indvandrere og efterkommere", "value": 'nondanishnonwestern'},
                    {"label": "Ikke-vestlige indvandrere og efterkommere", "value": 'nonwestern'},
                    ],
                value='all',
                id="health-heritage-selector",
            ),
        ], width=2),
        dbc.Col([
            dbc.Label(['Opnået højere uddannelse end grundskole?', button_help('health', '4')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Grundskole som højest fuldførte udd.", "value": 'unskilled'},
                    {"label": "Højere udd. end grundskole", "value": 'skilled'},
                ],
                value='all',
                id="health-labor-selector",
            ),
        ], width=2),
    	dbc.Col([
            dbc.Label(['Opnået videregående uddannelse?', button_help('health', '5')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Ingen videregående udd.", "value": 'low'},
                    {"label": "Opnået videregående udd.", "value": 'high'},
                ],
                value='all',
                id="health-education-selector",
            ),
        ], width=2),
        dbc.Col([
            dbc.Label('År:'),
            html.Div(
                dbc.Select(
                    id='health-year-selector',
                    options=[{'label': y, 'value': y} for y in df['year'].unique()],
                    value=2018,
                )
            ),
            html.Div([
                dbc.Button(
                    'Nulstil tidsserie',
                    id='health-clear-memory-button',
                    color='danger',
                    outline=True,
                    style={'marginBottom': '0.25em'}
                ),
                download_dropdown('health')]
            , style={'paddingTop': '0.25em'}),
        ], width=1)
    ]),
], fluid=True)

layout = html.Div([
    html.Div([top_banner()]),
    html.Div(id='id-guide', children=[
        html.Img(
            src='data:image/svg+xml;base64,{}'.format(encode_svg('guide-page.svg').decode())
        ),
    ]),
    html.Div([navigation2()]),
    html.Div(dcc.Store(id='health-memory')), # reverts to default on every page refresh
    html.Div(dcc.Store(id='health-color-memory')), # reverts to default on every page refresh
    html.Div([dbc.Fade(
        controls, id='health-control-fade', is_in=False, style={"transition": "opacity 200ms ease"}
    )
    ], id='health-control-panel', className='control_panel'),
    html.Div(
        dbc.Container([html.H4(id='health-title', style={'textAlign': 'center'}), html.H5(id='health-subtitle', style={'textAlign': 'center'})], fluid=True), id='health-title-div', style={'paddingBottom': '0.25em'}
    ),
    html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Container([
                    dcc.Loading(
                        type='circle',
                        children=[
                            dcc.Graph(
                                id='health-map-graph',
                                config={'displayModeBar': False},
                                clear_on_unhover=True,
                            ),
                        ]
                    )
                ], fluid=True)
            ]),
            dbc.Col([
                dbc.Container([
                    dcc.Loading(
                        type='circle',
                        children=[
                            dcc.Graph(
                                id='health-line-graph',
                                config={'displayModeBar': False},
                                clear_on_unhover=True
                            ),
                        ]
                    )
                ], fluid=True)
            ])
        ], no_gutters=True)
    ], style={'marginBottom': '2em'}),
])

### interactive content ###
@app.callback(
    [Output('health-control-panel', 'style'),
     Output('health-control-fade', 'is_in')],
    [Input('button-filtre', 'n_clicks')],
    [State('url', 'pathname')]
)
def show_hide_panel(clicks, pathname):
    if pathname == '/health':
        if clicks == None:
            return [{'display': 'none'}, False]
        elif clicks % 2 == 0:
            return [{'display': 'none'}, False]
        else:
            return [{'display': 'block'}, True]
    else:
        raise PreventUpdate

@app.callback(
    [Output("button-health", "style"),
     Output("icon-health", "src")],
    [Input("url", "pathname")],
)
def set_active_button(pathname):
    if pathname == "/health":
        return [{'backgroundColor':RF_orange, 'borderColor': RF_orange, 'color': 'rgb(255, 255, 255)'}, 'data:image/svg+xml;base64,{}'.format(health_icon_active.decode())]
    else:
        return [{'backgroundColor':'rgb(255,255,255)', 'borderColor': 'rgb(51,51,51)', 'color': 'rgb(51,51,51)'}, 'data:image/svg+xml;base64,{}'.format(health_icon.decode())]

@app.callback(
    [Output('health-title', 'children'),
     Output('health-subtitle', 'children')],
    [Input('health-variable-selector', 'value'),
    Input('health-measure-selector', 'value'),
    Input('health-gender-selector', 'value'),
    Input('health-age-selector', 'value'),
    Input('health-heritage-selector', 'value'),
    Input('health-education-selector', 'value'),
    Input('health-labor-selector', 'value'),
    Input('health-year-selector', 'value')]
)
def update_title(selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, selected_year):
    if selected_variable == 'copd' and selected_measure == 'mean':
        header = 'Figurerne viser udvikling i KOL-diagnoser målt som gennemsnit'
    elif selected_variable == 'copd' and selected_measure == 'Gini' or selected_measure.startswith('Theil') or selected_measure[1].isdigit():
        header = f'Figurerne viser ulighed i KOL-diagnoser  målt ved {labels_dict[selected_measure]}'
    elif selected_measure == 'Gini' or selected_measure.startswith('Theil') or selected_measure[1].isdigit():
        header = f'Figurerne viser ulighed i {labels_dict[selected_variable].lower()} målt ved {labels_dict[selected_measure]}'
    elif selected_measure == 'mean':
        header = f'Figurerne viser udvikling i gennemsnitlig {labels_dict[selected_variable].lower()}'
    elif selected_variable == 'copd' and selected_measure == 'mean':
        header = 'Figurerne viser udvikling i KOL-diagnoser målt som gennemsnit'
    elif selected_measure == 'copd':
        header = 'Figurerne viser ulighed i KOL-diagnoser'
    else:
        header = f'Figurerne viser ulighed i {labels_dict[selected_variable].lower()} målt ved {labels_dict[selected_measure].lower()}'
    if any(t != 'all' for t in [selected_gender, selected_age, selected_heritage, selected_education, selected_labor]):
        txt2 = '\nResultaterne er udregnet for '
    else:
        txt2 = ''
    #### Gender ####
    if selected_gender != 'all' and selected_heritage == 'all':
        txt_g = f'{labels_dict[selected_gender]}'
    elif selected_gender != 'all' and selected_heritage == 'danish':
        txt_g = f'{labels_dict[selected_gender]}'
    elif selected_gender != 'all':
        txt_g = f'{labels_dict[labels_dict[selected_gender]]}'
    else:
        txt_g = ''
    #### Age ####
    if selected_age == 'age5' and selected_gender == selected_heritage == 'all':
        txt_a = f'befolkningen {health_age_dict[selected_age]} ' # health_age_dict
    elif selected_age == 'age5':
        txt_a = f' {health_age_dict[selected_age]} '
    elif selected_age != 'all' and selected_gender == selected_heritage == 'all':
        txt_a = f'befolkningen mellem {health_age_dict[selected_age]} år' # health_age_dict
    elif selected_age != 'all':
        txt_a = f' mellem {health_age_dict[selected_age]} år'
    else:
        txt_a = ''
    #### Heritage ####
    if selected_heritage == 'danish' and selected_gender != 'all':
        txt_h = f'{labels_dict[labels_dict[selected_heritage]]}'
    elif selected_heritage != 'all':
        txt_h = f'{labels_dict[selected_heritage]}'
    else:
        txt_h = ''
    #### Labor ####
    if selected_education == 'high':
        txt_l = ''
    elif selected_labor != 'all' and selected_gender == selected_age == selected_heritage == 'all':
        txt_l = f'befolkningen, som har {labels_dict[selected_labor]}'
    elif selected_labor != 'all':
        txt_l = f'{labels_dict[selected_labor]}'
    else:
        txt_l = ''
    #### Education ####
    if selected_labor == 'unskilled':
        txt_e = ''
    elif selected_education != 'all' and selected_gender == selected_age == selected_heritage == selected_labor == 'all':
        txt_e = f'befolkningen, som har {labels_dict[selected_education]}'
    elif selected_education != 'all' and selected_gender == selected_age == selected_heritage == 'all' and selected_labor == 'skilled':
        txt_e = f'befolkningen, som har {labels_dict[selected_education]}'
    elif selected_education != 'all':
        txt_e = f'{labels_dict[selected_education]}'
    else:
        txt_e = ''
    #### combine ####
    if selected_heritage == 'danish' and selected_gender != 'all':
        sub_txt1 = ' '.join(filter(None, [txt_h, txt_g, txt_a]))
    else:
        sub_txt1 = ' '.join(filter(None, [txt_g, txt_h, txt_a]))
    sub_txt2 = ' og '.join(filter(None, [txt_l, txt_e]))
    sub_txt = ', som har '.join(filter(None,[sub_txt1, sub_txt2]))
    sub_header = txt2 + sub_txt
    return header, sub_header

for i in range(6):
    @app.callback(
        Output(f'health-help-text{i}', 'is_open'),
        [Input(f'health-open-help{i}', 'n_clicks'),
         Input(f'health-close-help{i}', 'n_clicks')],
        [State(f'health-help-text{i}', 'is_open')]
    )
    def open_help_text(c1, c2, is_open):
        if c1 or c2:
            return not is_open
        else:
            return is_open

@app.callback(
    [Output('health-help-header0', 'children'),
     Output('health-help-body0', 'children')],
    [Input('health-variable-selector', 'value')]
)
def txt_help_button0(var):
    health_help_labels0 = {
        'admissions': html.P(['Dette mål for sundhed angiver, hvor mange gange en person er blevet indlagt på et hospital det pågældende år. Ambulante indlæggelser og deldøgnsindlæggelser er ikke medtaget, så målet angiver kun heldøgnsindlæggelser. Indlæggelser i forbindelse med fødsel og graviditet er ikke inkluderet.']),

        'nights': html.P(['Dette mål for sundhed angiver, hvor mange dage en person har været indlagt på et hospital det pågældende år. Indlæggelser i forbindelse med fødsel og graviditet er ikke inkluderet.']),

        'gp': html.P(['.']),

        'copd': html.P(['.']),

        't2diabetes': html.P(['.']),
    }
    return labels_dict[var], health_help_labels0[var]

@app.callback(
    [Output('health-help-header1', 'children'),
     Output('health-help-body1', 'children')],
    [Input('health-measure-selector', 'value')]
)
def txt_help_button1(val):
    health_help_labels1 = {
        'Gini': html.P(["Dette mål for ulighed angiver i hvilken grad dårlig sundhed er koncentreret hos en lille gruppe eller jævnt fordelt. En højere Gini-koefficient betyder mere ulighed: hvis alle personer for eksempel har været indlagt præcist lige mange gange, er Gini-koefficienten 0 og hvis én enkelt person står for alle hospitalsindlæggelser, er Gini-koefficienten 1.", html.Br(), html.Br(), "Læs mere ", html.A('her', href='https://da.wikipedia.org/wiki/Gini-koefficient', target='_blank'), ' og ', html.A('her', href='https://denstoredanske.lex.dk/gini-koefficient', target='_blank'), '.']),

        'mean': html.P(["Dette mål angiver ikke ulighed i sig selv, men opgør gennemsnitlig sundhed. Målet er udregnet som et simpelt gennemsnit af det valgte mål for sundhed for den pågældende gruppe og inden for hver enkelt kommune."]),

        'diff_gender': html.P(["Dette mål opgør forskelle i det valgte mål for sundhed mellem mænd og kvinder. Målet er udregnet ved at trække kvinders sundhedsmål fra mænds, og en positiv værdi betyder således, at mænd i gennemsnit har flere indlæggelser eller dage på hospital end kvinder."]),

        'diff_heritage': html.P(["Dette mål opgør forskelle i det valgte mål for sundhed mellem danskere og indvandrere/efterkommere. Målet er udregnet ved at trække indvandrere og efterkommeres sundhedsmål fra danskeres, og en positiv værdi betyder således, at danskere i gennemsnit har flere indlæggelser eller dage på hospital end indvandrere eller efterkommere."]),

        'diff_labor': html.P(["Dette mål opgør forskellen i sundhed mellem personer med og uden højere uddannelse end grundskolen. Målet er udregnet ved at trække det valgte mål for sundhed for personer uden højere uddannelse end grundskolen fra det valgte mål for sundhed for personer med højere uddannelse end grundskolen. En positiv værdi betyder således, at personer med højere uddannelse end grundskolen i gennemsnit har flere indlæggelser eller dage på hospital end personer uden."]),

        'diff_education': html.P(["Dette mål opgør forskelle i det valgte mål for sundhed mellem personer med og uden videregående uddannelse. Målet er udregnet ved at trække det valgte mål for sundhed for personer uden videregående uddannelse fra det valgte mål for sundhed for personer med videregående uddannelse, og en positiv værdi betyder således, at personer med videregående uddannelse i gennemsnit har flere indlæggelser eller dage på hospital end personer uden."]),
    }
    return labels_dict[val], health_help_labels1[val]

@app.callback(
    [Output('health-help-header2', 'children'),
     Output('health-help-body2', 'children')],
     [Input('health-gender-selector', 'value')]
)
def txt_help_button2(_):
    return 'Køn', html.P(["Information om køn er baseret på CPR-nummers sidste ciffer.", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/TilSalg/Forskningsservice/Dokumentation/hoejkvalitetsvariable/folketal/koen', target='_blank'),'.'])

@app.callback(
    [Output('health-help-header3', 'children'),
     Output('health-help-body3', 'children')],
     [Input('health-heritage-selector', 'value')]
)
def txt_help_button3(_):
    return 'Herkomst', html.P(["Indvandrere er defineret som personer, der er født i udlandet og hvor ingen af forældrene er både danske statsborgere og født i Danmark. Efterkommere er personer, som er født i Danmark og hvor ingen af forældrene er både danske statsborgere og født i Danmark. Danskerne udgør resten af befolkningen.", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/TilSalg/Forskningsservice/Dokumentation/hoejkvalitetsvariable/udlaendinge/ie-type', target='_blank'),'.'])

@app.callback(
    [Output('health-help-header4', 'children'),
     Output('health-help-body4', 'children')],
     [Input('health-labor-selector', 'value')]
)
def txt_help_button4(_):
    return 'Opnået højere uddannelse end grundskole?', html.P(["Angiver om personen har fuldført anden uddannelse end grundskole og forberedende uddannelser. Påbegyndte, uafsluttede uddannelser tæller ikke med, kun fuldførte uddannelser.", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/uddannelsesdata/befolkningens-uddannelse', target='_blank'),'.'])

@app.callback(
    [Output('health-help-header5', 'children'),
     Output('health-help-body5', 'children')],
     [Input('health-labor-selector', 'value')]
)
def txt_help_button5(_):
    return 'Opnået videregående uddannelse?', html.P(["Videregående uddannelser inkluderer både korte videregående uddannelser (KVU, fx pædagog), mellemlange videregående uddannelser (MVU, fx skolelærer), lange videregående uddannelser (LVU, fx læge) og forskeruddannelser (ph.d.).", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/uddannelsesdata/befolkningens-uddannelse', target='_blank'),'.'])

@app.callback(
    Output('health-education-selector', 'value'),
    [Input('health-measure-selector', 'value'),
    Input('health-labor-selector', 'value')]
)
def education_correction(msr, lab):
    if msr == 'diff_labor' or msr == 'diff_education':
        return 'all'
    elif lab == 'unskilled':
        return 'low'
    else:
        raise PreventUpdate

@app.callback(
    [Output('health-measure-selector', 'options'),
     Output('health-measure-selector', 'value')],
    [Input('health-variable-selector', 'value')],
    [State('health-measure-selector', 'value')]
)

def disable_measure(var, stt):
    if (var == 'admissions' or var == 'nights' or var == 'gp') and stt.startswith('T'):
        return [
            {'label': labels_dict['Gini'], 'value': 'Gini'},
            {'label': labels_dict['Theil_L'], 'value': 'Theil_L', 'disabled':True},
            {'label': labels_dict['Theil_T'], 'value': 'Theil_T', 'disabled':True},
            {'label': labels_dict['mean'], 'value': 'mean'},
            {'label': labels_dict['diff_gender'], 'value': 'diff_gender'},
            {'label': labels_dict['diff_heritage'], 'value': 'diff_heritage'},
            {'label': labels_dict['diff_labor'], 'value': 'diff_labor'},
            {'label': labels_dict['diff_education'], 'value': 'diff_education'},
        ], 'Gini'

    elif (var == 'admissions' or var == 'nights' or var == 'gp'):
        return [
            {'label': labels_dict['Gini'], 'value': 'Gini'},
            {'label': labels_dict['Theil_L'], 'value': 'Theil_L', 'disabled':True},
            {'label': labels_dict['Theil_T'], 'value': 'Theil_T', 'disabled':True},
            {'label': labels_dict['mean'], 'value': 'mean'},
            {'label': labels_dict['diff_gender'], 'value': 'diff_gender'},
            {'label': labels_dict['diff_heritage'], 'value': 'diff_heritage'},
            {'label': labels_dict['diff_labor'], 'value': 'diff_labor'},
            {'label': labels_dict['diff_education'], 'value': 'diff_education'},
        ], stt

    else:
        return [
            {'label': labels_dict['Gini'], 'value': 'Gini'},
            {'label': labels_dict['Theil_L'], 'value': 'Theil_L'},
            {'label': labels_dict['Theil_T'], 'value': 'Theil_T'},
            {'label': labels_dict['mean'], 'value': 'mean'},
            {'label': labels_dict['diff_gender'], 'value': 'diff_gender'},
            {'label': labels_dict['diff_heritage'], 'value': 'diff_heritage'},
            {'label': labels_dict['diff_labor'], 'value': 'diff_labor'},
            {'label': labels_dict['diff_education'], 'value': 'diff_education'},
        ], stt

@app.callback(
    [Output('health-heritage-selector', 'value'),
    Output('health-heritage-selector', 'options')],
    [Input('health-measure-selector', 'value')],
    [State('health-heritage-selector', 'value')]
)
def disable_heritage(msr, state):
    if msr == 'diff_heritage':
        return 'all', [
            {"label": "Alle", "value": "all"},
            {"label": "Dansk", "value": 'danish', 'disabled':True},
            {"label": "Indvandrere og efterkommere", "value": 'nondanishnonwestern', 'disabled':True},
            {"label": "Ikke-vestlige indvandrere og efterkommere", "value": 'nonwestern', 'disabled': True},
            ]
    else:
        return state, [
            {"label": "Alle", "value": "all"},
            {"label": "Dansk", "value": 'danish'},
            {"label": "Indvandrere og efterkommere", "value": 'nondanishnonwestern'},
            {"label": "Ikke-vestlige indvandrere og efterkommere", "value": 'nonwestern'},
            ]

@app.callback(
    [Output('health-gender-selector', 'value'),
    Output('health-gender-selector', 'options')],
    [Input('health-measure-selector', 'value')],
    [State('health-gender-selector', 'value')]
)
def disable_gender(msr, state):
    if msr == 'diff_gender':
        return 'all', [
            {"label": "Alle", "value": "all"},
            {"label": "Kvinder", "value": 'woman', 'disabled':True},
            {"label": "Mænd", "value": 'man', 'disabled':True},
            ]
    else:
        return state, [
            {"label": "Alle", "value": "all"},
            {"label": "Kvinder", "value": 'woman'},
            {"label": "Mænd", "value": 'man'},
        ]

@app.callback(
    Output('health-education-selector', 'options'),
    [Input('health-labor-selector', 'value'),
     Input('health-measure-selector', 'value')],
)
def disable_education(opt, msr):
    if msr == 'diff_labor' or msr == 'diff_education':
        return [
            {"label": "Alle", "value": "all"},
            {"label": "Ingen videregående udd.", "value": 'low',  'disabled':True},
            {"label": "Opnået videregående udd.", "value": 'high', 'disabled':True},
        ]
    elif opt == 'unskilled':
        return [
            {"label": "Alle", "value": "all", 'disabled':True},
            {"label": "Ingen videregående udd.", "value": 'low'},
            {"label": "Opnået videregående udd.", "value": 'high', 'disabled':True},
        ]
    else:
        return [
            {"label": "Alle", "value": "all"},
            {"label": "Ingen videregående udd.", "value": 'low'},
            {"label": "Opnået videregående udd.", "value": 'high'},
        ]

@app.callback(
    [Output('health-labor-selector', 'options'),
     Output('health-labor-selector', 'value')],
    [Input('health-education-selector', 'value'),
     Input('health-measure-selector', 'value')],
    [State('health-labor-selector', 'value')]
)
def disable_labor(opt, msr, state):
    if msr == 'diff_labor' or msr == 'diff_education':
        return [
            {"label": "Alle", "value": "all"},
            {"label": "Grundskole som højest fuldførte udd.", "value": 'unskilled', 'disabled':True},
            {"label": "Højere udd. end grundskole", "value": 'skilled', 'disabled':True},
        ], 'all'
    elif opt == 'high':
        return [
            {"label": "Alle", "value": "all", 'disabled':True },
            {"label": "Grundskole som højest fuldførte udd.", "value": 'unskilled', 'disabled':True},
            {"label": "Højere udd. end grundskole", "value": 'skilled'},
        ], 'skilled'
    else:
        return [
            {"label": "Alle", "value": "all"},
            {"label": "Grundskole som højest fuldførte udd.", "value": 'unskilled'},
            {"label": "Højere udd. end grundskole", "value": 'skilled'},
        ], state

@app.callback(
    [Output('health-memory', 'clear_data'),
     Output('health-color-memory', 'clear_data')],
    [Input('health-clear-memory-button', 'n_clicks')]
)
def erase_memory(click):
    if click is None:
        raise PreventUpdate
    else:
        return True, True

@app.callback(
    Output('health-color-memory', 'data'),
    [Input('health-map-graph', 'clickData')],
    [State('health-color-memory', 'data')]
)
def get_colors(clickData, data):
    if clickData is None:
        raise PreventUpdate
    else:
        data = data or []
        if len(data) == 3:
            data.pop(0)
        if 'rgb(13,143,148)' not in data:
            data.append('rgb(13,143,148)')
            return data
        elif 'rgb(173,173,173)' not in data:
            data.append('rgb(173,173,173)')
            return data
        else:
            data.append('rgb(102,21,32)')
            return data

@app.callback(
    Output('health-memory', 'data'),
    [Input('health-map-graph', 'clickData')],
    [State('health-memory', 'data')]
)
def click_list(clickData, data):
    if clickData is None:
        raise PreventUpdate

    data = data or []
    if clickData['points'][0]['customdata'][0] not in data:
        data.append(clickData['points'][0]['customdata'][0])
    while len(data) > 3:
        data.pop(0)
    return data

@app.callback(
    Output('health-map-graph', 'figure'),
    [Input('health-variable-selector', 'value'),
    Input('health-measure-selector', 'value'),
    Input('health-gender-selector', 'value'),
    Input('health-age-selector', 'value'),
    Input('health-heritage-selector', 'value'),
    Input('health-education-selector', 'value'),
    Input('health-labor-selector', 'value'),
    Input('health-year-selector', 'value')]
)
def update_map(selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, selected_year):
    dfs = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor)].copy()
    dfs.dropna(axis=0, subset=[selected_measure], inplace=True)
    colorscale_level = ['rgb(244,230,211)', 'rgb(244,190,117)', 'rgb(242,146,12)', 'rgb(219,126,15)', 'rgb(196,105,18)', 'rgb(162,75,23)', 'rgb(102,21,32)', 'rgb(51,11,16)']

    rdf = pd.DataFrame(columns=['KOMKODE','val', 'municipality'])
    ### Get missing kommuner ###
    missing_mun_list = []
    for k in komkoder2str.keys():
        if k not in dfs['KOMKODE'].unique():
            missing_mun_list.append(k)
            rdf = rdf.append({'KOMKODE':k, 'municipality':komkoder2str.get(k), 'val':'missing'}, ignore_index=True)

    if selected_measure == 'diff_education':
        grp1 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == 'low') & (df['labor'] == selected_labor)]
        grp2 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == 'high') & (df['labor'] == selected_labor)]
        grp1 = grp1[~grp1['KOMKODE'].isin(missing_mun_list)]
        grp2 = grp2[~grp2['KOMKODE'].isin(missing_mun_list)]
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale='RdBu_r',
                            # range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: 'Antal'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.3f}<br>" +\
                "Antal uden videregående udd.: %{customdata[2]:,}<br>" +\
                "Antal med videregående udd.: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at dem med videregående uddannelse har dårligere sundhed)'
    elif selected_measure == 'diff_labor':
        grp1 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == 'unskilled')]
        grp2 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == 'skilled')]
        grp1 = grp1[~grp1['KOMKODE'].isin(missing_mun_list)]
        grp2 = grp2[~grp2['KOMKODE'].isin(missing_mun_list)]
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale='RdBu_r',
                            # range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: 'Antal'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.3f}<br>" +\
                "Antal m. grundskole som højest fuldførte udd.: %{customdata[2]:,}<br>" +\
                "Antal m. højere udd. end grundskole: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at dem m. højere udd. end grundskole har dårligere sundhed)'
    elif selected_measure == 'diff_gender':
        grp1 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == 'woman') & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor)]
        grp2 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == 'man') & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor)]
        grp1 = grp1[~grp1['KOMKODE'].isin(missing_mun_list)]
        grp2 = grp2[~grp2['KOMKODE'].isin(missing_mun_list)]
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale='RdBu_r',
                            # range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: 'Antal'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.3f}<br>" +\
                "Antal kvinder: %{customdata[2]:,}<br>" +\
                "Antal mænd: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at mænd har dårligere sundhed)'
    elif selected_measure == 'diff_heritage':
        grp1 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == 'danish') & (df['education'] == selected_education) & (df['labor'] == selected_labor)]
        grp2 = df[(df['variable'] == selected_variable) & (df['year'] == int(selected_year)) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == 'nonwestern') & (df['education'] == selected_education) & (df['labor'] == selected_labor)]
        grp1 = grp1[~grp1['KOMKODE'].isin(missing_mun_list)]
        grp2 = grp2[~grp2['KOMKODE'].isin(missing_mun_list)]
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale='RdBu_r',
                            # range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: 'Antal'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.3f}<br>" +\
                "Antal danskere: %{customdata[2]:,}<br>" +\
                "Antal ikke-vestlige indvandrere og efterkommere: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at danskere har dårligere sundhed)'
    elif selected_measure == 'Gini' or selected_measure.startswith('Theil_') or selected_measure[1].isdigit():
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale=colorscale_level,
                            range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: ''},
                            # color_continuous_midpoint=np.mean(dfs[selected_measure]),
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], dfs['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.4f}<br>" +\
                "Antal observationer: %{customdata[2]:,}"
            )
        )
    elif (selected_variable == 'copd' or selected_variable == 't2diabetes') and (selected_measure == 'mean'):
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale=colorscale_level,
                            range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: 'Procent'},
                            # color_continuous_midpoint=np.median(dfs[selected_measure]),
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], dfs['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.3f}<br>" +\
                "Antal observationer: %{customdata[2]:,}"
            )
        )
    elif selected_measure == 'mean':
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale=colorscale_level,
                            range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: 'Antal'},
                            # color_continuous_midpoint=np.median(dfs[selected_measure]),
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], dfs['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.3f}<br>" +\
                "Antal observationer: %{customdata[2]:,}"
            )
        )

    else:
        fig = px.choropleth(dfs, geojson=geojson, color=selected_measure,
                            locations="KOMKODE",
                            featureidkey="properties.KOMKODE",
                            projection="mercator",
                            color_continuous_scale=colorscale_level,
                            range_color=[dfs[selected_measure].min(), dfs[selected_measure].max()],
                            labels={selected_measure: ''},
                            # color_continuous_midpoint=np.median(dfs[selected_measure]),
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], dfs['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.3f}<br>" +\
                "Antal observationer: %{customdata[2]:,}"
            )
        )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        font_family='Avenir Next',
        # title_text='Hello world',
        # width=1000,
        # height=600,
        margin={"r":0,"t":0,"l":0,"b":0},
        font_size=12,
        coloraxis_colorbar_tickformat='',
        separators=",..",
        autosize=True,
        coloraxis=dict(
            colorbar_x=-0.05
        ),
    )

    ##### Add square around Bornholm #####
    factorx = 0.1
    factory = 0.065
    x = [12.682574-factorx, 12.682574-factorx, 13.193236+factorx, 13.193236+factorx, 12.682574-factorx]
    y = [56.986583-factory, 57.323286+factory, 57.323286+factory, 56.986583-factory, 56.986583-factory]
    Bsquare = px.line_geo(lat=y, lon=x, projection='mercator',  color_discrete_sequence=['rgb(0,0,0)']*5)
    Bsquare.data[0].showlegend=False
    Bsquare.update_traces(
       hovertemplate=None,
       hoverinfo='skip'
    )
    fig.add_trace(Bsquare.data[0])
    anno_text1 = f'År: {selected_year}'
    if 'anno_text2' not in locals():
            anno_text2 = ''
    anno_text_final = '<br>'.join(filter(None, [anno_text1, anno_text2]))
    fig.add_annotation(x=0.5, y=0, text=anno_text_final, showarrow=False)

    if len(rdf) > 0: # if some municipalities are missing
        missing_map = px.choropleth(rdf, geojson=geojson, color="val",
                            locations="KOMKODE", featureidkey="properties.KOMKODE",
                            projection="mercator", color_discrete_map={'missing':'gray'},
                           )
        missing_map.data[0].showlegend=False
        missing_map.update_traces(
            customdata= np.stack((rdf['municipality'], rdf['val']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Få observationer" + \
                "<extra></extra>"
            )
        )

        fig.add_trace(missing_map.data[0])
    return fig
@app.callback(
    Output('health-line-graph', 'figure'),
    [
    Input('health-variable-selector', 'value'),
    Input('health-measure-selector', 'value'),
    Input('health-gender-selector', 'value'),
    Input('health-age-selector', 'value'),
    Input('health-heritage-selector', 'value'),
    Input('health-education-selector', 'value'),
    Input('health-labor-selector', 'value'),
    Input('health-memory', 'data'),
    Input('health-color-memory', 'data'),
    ]
)
def update_line_graph(selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, clickData, color):
    dfs = df[(df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor) & (df['variable'] == selected_variable)]

    line_all = dfs[dfs['KOMKODE'] == 0]
    hele_danmark_color = 'rgb(242,146,12)'
    fig = go.Figure()


    ##### section for diff_* maps #####
    if selected_measure == 'diff_education':
        grp1 = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == selected_heritage) & (df['education'] == 'low') & (df['labor'] == selected_labor)]['observations'])
        grp2 = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == selected_heritage) & (df['education'] == 'high') & (df['labor'] == selected_labor)]['observations'])

        fig.add_trace(go.Scatter(x=df['year'].unique(), y=line_all[selected_measure], name='Hele Danmark',
                                mode='lines', line=dict(color=hele_danmark_color),
                                meta=[f'Antal uden videregående udd.: {format(int(grp1[i]), ",d").replace(",", ".")} <br>Antal med videregående udd.: {format(int(grp2[i]), ",d").replace(",", ".")}' for i in range(len(grp1))],
                                hovertemplate=
                                    '<b>Hele Danmark</b><br>'+
                                    '%{x}: '+
                                    '%{y:,.3f} <br>'+
                                    '%{meta}'
                                    "<extra></extra>"
                                 ))

        if clickData is not None:
            for l in range(len(clickData)):
                dfl = dfs[dfs['municipality'] == clickData[l]]
                grp1l = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == selected_heritage) & (df['education'] == 'low') & (df['labor'] == selected_labor)]['observations'])
                grp2l = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == selected_heritage) & (df['education'] == 'high') & (df['labor'] == selected_labor)]['observations'])

                fig.add_trace(go.Scatter(x=df['year'].unique(), y=dfl[selected_measure],
                name=clickData[l],
                mode='lines', line=dict(color=color[l]),
                meta=clickData[l],
                text=[f'Antal uden videregående udd.: {format(grp1l[i], ",g").replace(",", ".")} <br>Antal med videregående udd.: {format(grp2l[i], ",g").replace(",", ".")}' for i in range(len(grp1l))],
                hovertemplate=
                    '<b>%{meta}</b><br>'+
                    '%{x}: '+
                    '%{y:,.3f} <br>'+
                    '%{text}'
                    "<extra></extra>"
                ))

    elif selected_measure == 'diff_labor':
        grp1 = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == 'unskilled')]['observations'])
        grp2 = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == 'skilled')]['observations'])

        fig.add_trace(go.Scatter(x=df['year'].unique(), y=line_all[selected_measure], name='Hele Danmark',
                                mode='lines', line=dict(color=hele_danmark_color),
                                text=[f'Antal m. grundskole som højest fuldførte udd.: {format(int(grp1[i]), ",d").replace(",", ".")} <br>Antal m. højere udd. end grundskole: {format(int(grp2[i]), ",d").replace(",", ".")}' for i in range(len(grp1))],
                                hovertemplate=
                                    '<b>Hele Danmark</b><br>'+
                                    '%{x}: '+
                                    '%{y:,.3f} <br>'+
                                    '%{text}'
                                    "<extra></extra>"
                                 ))

        if clickData is not None:
            for l in range(len(clickData)):
                dfl = dfs[dfs['municipality'] == clickData[l]]
                grp1l = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == 'unskilled')]['observations'])
                grp2l = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == 'skilled')]['observations'])

                fig.add_trace(go.Scatter(x=df['year'].unique(), y=dfl[selected_measure],
                name=clickData[l],
                mode='lines', line=dict(color=color[l]),
                meta=clickData[l],
                text=[f'Antal m. grundskole som højest fuldførte udd.: {format(grp1l[i], ",g").replace(",", ".")} <br>Antal m. højere udd. end grundskole: {format(grp2l[i], ",g").replace(",", ".")}' for i in range(len(grp1l))],
                hovertemplate=
                    '<b>%{meta}</b><br>'+
                    '%{x}: '+
                    '%{y:,.3f} <br>'+
                    '%{text}'
                    "<extra></extra>"
                ))
    elif selected_measure == 'diff_gender':
        grp1 = list(df[(df['variable'] == selected_variable) & (df['gender'] == 'woman') & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])
        grp2 = list(df[(df['variable'] == selected_variable) & (df['gender'] == 'man') & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])

        fig.add_trace(go.Scatter(x=df['year'].unique(), y=line_all[selected_measure], name='Hele Danmark',
                                mode='lines', line=dict(color=hele_danmark_color),
                                text=[f'Antal kvinder: {format(int(grp1[i]), ",d").replace(",", ".")} <br>Antal mænd: {format(int(grp2[i]), ",d").replace(",", ".")}' for i in range(len(grp1))],
                                hovertemplate=
                                    '<b>Hele Danmark</b><br>'+
                                    '%{x}: '+
                                    '%{y:,.3f} <br>'+
                                    '%{text}'
                                    "<extra></extra>"
                                 ))

        if clickData is not None:
            for l in range(len(clickData)):
                dfl = dfs[dfs['municipality'] == clickData[l]]
                grp1l = list(df[(df['variable'] == selected_variable) & (df['gender'] == 'woman') & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])
                grp2l = list(df[(df['variable'] == selected_variable) & (df['gender'] == 'man') & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == selected_heritage) & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])

                fig.add_trace(go.Scatter(x=df['year'].unique(), y=dfl[selected_measure],
                name=clickData[l],
                mode='lines', line=dict(color=color[l]),
                meta=clickData[l],
                text=[f'Antal kvinder: {format(grp1l[i], ",g").replace(",", ".")} <br>Antal mænd: {format(grp2l[i], ",g").replace(",", ".")}' for i in range(len(grp1l))],
                hovertemplate=
                    '<b>%{meta}</b><br>'+
                    '%{x}: '+
                    '%{y:,.3f} <br>'+
                    '%{text}'
                    "<extra></extra>"
                ))
    elif selected_measure == 'diff_heritage':
        grp1 = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == 'danish') & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])
        grp2 = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['KOMKODE'] == 0) & (df['heritage'] == 'nonwestern') & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])

        fig.add_trace(go.Scatter(x=df['year'].unique(), y=line_all[selected_measure], name='Hele Danmark',
                                mode='lines', line=dict(color=hele_danmark_color),
                                text=[f'Antal danskere: {format(int(grp1[i]), ",d").replace(",", ".")} <br>Antal ikke-vestlige indvandrere og efterkommere: {format(int(grp2[i]), ",d").replace(",", ".")}' for i in range(len(grp1))],
                                hovertemplate=
                                    '<b>Hele Danmark</b><br>'+
                                    '%{x}: '+
                                    '%{y:,.3f} <br>'+
                                    '%{text}'
                                    "<extra></extra>"
                                 ))

        if clickData is not None:
            for l in range(len(clickData)):
                dfl = dfs[dfs['municipality'] == clickData[l]]
                grp1l = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == 'danish') & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])
                grp2l = list(df[(df['variable'] == selected_variable) & (df['gender'] == selected_gender) & (df['age'] == selected_age) & (df['municipality'] == clickData[l]) & (df['heritage'] == 'nonwestern') & (df['education'] == selected_education) & (df['labor'] == selected_labor)]['observations'])

                fig.add_trace(go.Scatter(x=df['year'].unique(), y=dfl[selected_measure],
                name=clickData[l],
                mode='lines', line=dict(color=color[l]),
                meta=clickData[l],
                text=[f'Antal danskere: {format(grp1l[i], ",g").replace(",", ".")} <br>Antal ikke-vestlige indvandrere og efterkommere: {format(grp2l[i], ",g").replace(",", ".")}' for i in range(len(grp1l))],
                hovertemplate=
                    '<b>%{meta}</b><br>'+
                    '%{x}: '+
                    '%{y:,.3f} <br>'+
                    '%{text}'
                    "<extra></extra>"
                ))
    elif selected_measure == 'Gini' or selected_measure == 'Theil_L' or selected_measure == 'Theil_T' or selected_measure[1].isdigit():
        fig.add_trace(go.Scatter(x=df['year'].unique(), y=line_all[selected_measure], name='Hele Danmark',
                                mode='lines', line=dict(color=hele_danmark_color), meta=line_all['observations'],
                                hovertemplate=
                                '<b>Hele Danmark</b><br>'+
                                '%{x}: '+
                                '%{y:,.4f} <br>'+
                                'Antal observationer: %{meta:,}'
                                "<extra></extra>"
                                 ))

        if clickData is not None:
            for l in range(len(clickData)):
                dfl = dfs[dfs['municipality'] == clickData[l]]
                fig.add_trace(go.Scatter(x=df['year'].unique(), y=dfl[selected_measure],
                name=clickData[l],
                mode='lines', line=dict(color=color[l]),
                text=[f'{clickData[l]}' for _ in range(len(df['year'].unique()))],
                meta=dfl['observations'],
                hovertemplate=
                '<b>%{text}</b><br>'+
                '%{x}: '+
                '%{y:,.4f} <br>'+
                'Antal observationer: %{meta:,}'
                "<extra></extra>"))
    else:
        fig.add_trace(go.Scatter(x=df['year'].unique(), y=line_all[selected_measure], name='Hele Danmark',
                                mode='lines', line=dict(color=hele_danmark_color), meta=line_all['observations'],
                                hovertemplate=
                                '<b>Hele Danmark</b><br>'+
                                '%{x}: '+
                                '%{y:,.3f} <br>'+
                                'Antal observationer: %{meta:,}'
                                "<extra></extra>"
                                 ))

        if clickData is not None:
            for l in range(len(clickData)):
                dfl = dfs[dfs['municipality'] == clickData[l]]
                fig.add_trace(go.Scatter(x=df['year'].unique(), y=dfl[selected_measure],
                name=clickData[l],
                mode='lines', line=dict(color=color[l]),
                text=[f'{clickData[l]}' for _ in range(len(df['year'].unique()))],
                meta=dfl['observations'],
                hovertemplate=
                '<b>%{text}</b><br>'+
                '%{x}: '+
                '%{y:,.3f} <br>'+
                'Antal observationer: %{meta:,}'
                "<extra></extra>"))

    if (selected_variable == 'copd' or selected_variable == 't2diabetes') and (selected_measure == 'mean'):
         fig.update_layout(
             yaxis_title='Procent',
             yaxis_tickformat='',
         )
    elif selected_measure == 'mean' or selected_measure.startswith('diff'):
        fig.update_layout(
            yaxis_title='Antal',
            yaxis_tickformat='',
        )
    else:
        fig.update_layout(
            yaxis_title=None,
            yaxis_tickformat='',
        )
        fig.update_yaxes(nticks=7)
    fig.update_layout(
        xaxis_tickformat='date',
        font_family="Avenir Next",
        showlegend=True,
        separators=",..",
        plot_bgcolor=RF_gray,
        margin=dict(t=30,l=30,b=30,r=30),
        height=450,
        autosize=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.12,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


@app.callback(
    Output('health-download-csv-map', 'href'),
    [Input('health-download-csv-map-button', 'n_clicks'),
     Input('health-variable-selector', 'value'),
     Input('health-measure-selector', 'value'),
     Input('health-gender-selector', 'value'),
     Input('health-age-selector', 'value'),
     Input('health-heritage-selector', 'value'),
     Input('health-education-selector', 'value'),
     Input('health-labor-selector', 'value'),
     Input('health-year-selector', 'value')]
)
def health_link_download_map(click, selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, selected_year):
    query_params = {'variable': selected_variable,
                    'measure': selected_measure,
                    'gender': selected_gender,
                    'age': selected_age,
                    'heritage': selected_heritage,
                    'education': selected_education,
                    'labor': selected_labor,
                    'year': selected_year
                    }
    query_string = urllib.parse.urlencode(query_params, doseq=True)
    return f"/downloadHealthMap?{query_string}" # /dash/urlToDownload?

@app.server.route('/downloadHealthMap') # /dash/urlToDownload?
def health_download_map_csv():
    variable = flask.request.args.get('variable')
    measure = flask.request.args.get('measure')
    gender = flask.request.args.get('gender')
    age = flask.request.args.get('age')
    heritage = flask.request.args.get('heritage')
    education = flask.request.args.get('education')
    labor = flask.request.args.get('labor')
    year = flask.request.args.get('year')
    dff = df[(df['variable'] == variable) & (df['year'] == int(year)) & (df['gender'] == gender) & (df['age'] == age) & (df['heritage'] == heritage) & (df['education'] == education) & (df['labor'] == labor)].copy()
    df_out = dff[['KOMKODE', 'observations', 'year', measure]]

    str_io = io.StringIO()
    df_out.to_csv(str_io, index=False, header=['kommunekode', 'antal observationer', 'aar', 'vaerdi'])

    mem = io.BytesIO()
    mem.write(str_io.getvalue().encode('utf-8'))
    mem.seek(0)
    str_io.close()
    return flask.send_file(mem,
                           mimetype='text/csv',
                           attachment_filename='RFF-kort.csv',
                           as_attachment=True,
                           cache_timeout=0
    )

@app.callback(
    Output('health-download-csv-series', 'href'),
    [Input('health-download-csv-series-button', 'n_clicks'),
     Input('health-variable-selector', 'value'),
     Input('health-measure-selector', 'value'),
     Input('health-gender-selector', 'value'),
     Input('health-age-selector', 'value'),
     Input('health-heritage-selector', 'value'),
     Input('health-education-selector', 'value'),
     Input('health-labor-selector', 'value'),
     Input('health-memory', 'data')]
)
def health_link_download_series(click, selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, municipalities):
    if municipalities is not None:
        municipalities = [komstr2koder[m] for m in municipalities]
        municipalities.append(0)
    else:
        municipalities = [0]
    query_params = {'variable': selected_variable,
                    'measure': selected_measure,
                    'gender': selected_gender,
                    'age': selected_age,
                    'heritage': selected_heritage,
                    'education': selected_education,
                    'labor': selected_labor,
                    'municipalities': municipalities
                    }
    query_string = urllib.parse.urlencode(query_params, doseq=True)
    return f"/downloadHealthSeries?{query_string}" # /dash/urlToDownload?

@app.server.route('/downloadHealthSeries') # /dash/urlToDownload?
def health_download_series_csv():
    variable = flask.request.args.get('variable')
    measure = flask.request.args.get('measure')
    gender = flask.request.args.get('gender')
    age = flask.request.args.get('age')
    heritage = flask.request.args.get('heritage')
    education = flask.request.args.get('education')
    labor = flask.request.args.get('labor')
    municipalities = [int(m) for m in flask.request.args.getlist('municipalities')]

    dff = df[(df['variable'] == variable) & (df['gender'] == gender) & (df['age'] == age) & (df['heritage'] == heritage) & (df['education'] == education) & (df['labor'] == labor) & (df['KOMKODE'].isin(municipalities))].copy()
    df_out = dff[['KOMKODE', 'observations', 'year', measure]]

    str_io = io.StringIO()
    df_out.to_csv(str_io, index=False, header=['kommunekode', 'antal observationer', 'aar', 'vaerdi'])

    mem = io.BytesIO()
    mem.write(str_io.getvalue().encode('utf-8'))
    mem.seek(0)
    str_io.close()
    return flask.send_file(mem,
                           mimetype='text/csv',
                           attachment_filename='RFF-serie.csv',
                           as_attachment=True,
                           cache_timeout=0
    )

@app.callback(
    Output('health-download-png-series', 'href'),
    [Input('health-download-png-series-button', 'n_clicks'),
     Input('health-line-graph', 'figure')]
 )
def health_link_download_series_image(click, fig):
    if fig is None:
        raise PreventUpdate
    else:
        img_bytes = plotly.io.to_image(fig, format='png', engine='kaleido') # img as bytes
        out = base64.b64encode(img_bytes) # encoded
        query_param = {'encoding': out}
        query_string = urllib.parse.urlencode(query_param, doseq=True)
        return f"/downloadHealthSeriesImg?{query_string}"

@app.server.route('/downloadHealthSeriesImg')
def health_download_series_img():
    encoding = flask.request.args.get('encoding').encode('utf-8') # load as string and encode to bytes
    decoded = base64.b64decode(encoding)
    img_io = io.BytesIO(decoded)
    img_io.seek(0)
    return flask.send_file(img_io,
                           mimetype='image/png',
                           attachment_filename='RFF-serie.png',
                           as_attachment=True,
                           cache_timeout=0
    )

@app.callback(
    Output('health-download-png-map', 'href'),
    [Input('health-download-png-map-button', 'n_clicks'),
     Input('health-map-graph', 'figure')]
 )
def health_link_download_map_image(click, fig):
    if fig is None:
        raise PreventUpdate
    else:
        img_bytes = plotly.io.to_image(fig, format='png', engine='kaleido') # img as bytes
        out = base64.b64encode(img_bytes) # encoded
        query_param = {'encoding': out}
        query_string = urllib.parse.urlencode(query_param, doseq=True)
        return f"/downloadHealthMapImg?{query_string}"

@app.server.route('/downloadHealthMapImg')
def health_download_map_img():
    encoding = flask.request.args.get('encoding').encode('utf-8') # load as string and encode to bytes
    decoded = base64.b64decode(encoding)
    img_io = io.BytesIO(decoded)
    img_io.seek(0)
    return flask.send_file(img_io,
                           mimetype='image/png',
                           attachment_filename='RFF-kort.png',
                           as_attachment=True,
                           cache_timeout=0
    )


# print(px.colors.sequential.RdBu_r)
