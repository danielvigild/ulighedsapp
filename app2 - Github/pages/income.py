import io
import json
import urllib
import base64
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
    # get_highlights,
    # get_coordinates
)

### load in data ###
with open(path2file('kommuner4.geojson')) as geo:
    geojson = json.load(geo)
# district_lookup = {feature['properties']['KOMKODE']: feature for feature in geojson['features']} # dict for kommuner with KOMKODE as key and coordinates as value
with open(path2file('kommune_koder.json'), encoding='utf-8') as komk:
    komkoder  = json.load(komk)
komkoder2str = {int(k): str(v) for k, v in komkoder.items()}
komstr2koder = {str(v): int(k) for k, v in komkoder.items()}

df = pd.read_csv(path2file('income.csv'))
df = df.astype({'KOMKODE':'int', 'year':'int'}) # ensure correct type
df = df.sort_values(by=['year', 'KOMKODE'])

income_icon = encode_svg('inc_dark.svg')
income_icon_active = encode_svg('inc_orange.svg')

### begin layout ###
controls = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Label(['Indkomstmål:', button_help('income', '0')]),
            dbc.Select(
               id='income-variable-selector',
               options=[
                    {'label': labels_dict['aekvivadisp'], 'value': 'aekvivadisp'},
                    {'label': labels_dict['dispon'], 'value': 'dispon'},
                    {'label': labels_dict['perindkialt'], 'value': 'perindkialt'},
                    {'label': labels_dict['loenmv'], 'value': 'loenmv'}
               ],
               value='aekvivadisp',
            ),
            dbc.Label(['Målt ved:', button_help('income', '1')]),
            dbc.Select(
               id='income-measure-selector',
               value='Gini',
            ),
        ], width=3),
    	dbc.Col([
            dbc.Label(['Køn:', button_help('income', '2')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Kvinder", "value": 'woman'},
                    {"label": "Mænd", "value": 'man'},
                ],
                value='all',
                id="income-gender-selector",
            ),
        ], width=1),
        dbc.Col([
            dbc.Label(['Alder:',  button_help('income', '6')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "30-39 år", "value": 'age1'},
                    {"label": "40-49 år", "value": 'age2'},
                    {"label": "50-59 år", "value": 'age3'},
                    {"label": "60-65 år", "value": 'age4'},
                ],
                value='all',
                id="income-age-selector",
            ),
        ], width=1),
        dbc.Col([
            dbc.Label(['Herkomst:', button_help('income', '3')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Dansk", "value": 'danish'},
                    {"label": "Indvandrere og efterkommere", "value": 'nondanishnonwestern'},
                    {"label": "Ikke-vestlige indvandrere og efterkommere", "value": 'nonwestern'},
                    ],
                value='all',
                id="income-heritage-selector",
            ),
        ], width=2),
        dbc.Col([
            dbc.Label(['Opnået højere uddannelse end grundskole?', button_help('income', '4')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Grundskole som højest fuldførte udd.", "value": 'unskilled'},
                    {"label": "Højere udd. end grundskole", "value": 'skilled'},
                ],
                value='all',
                id="income-labor-selector",
            ),
        ], width=2),
    	dbc.Col([
            dbc.Label(['Opnået videregående uddannelse?', button_help('income', '5')]),
            dbc.RadioItems(
                options=[
                    {"label": "Alle", "value": "all"},
                    {"label": "Ingen videregående udd.", "value": 'low'},
                    {"label": "Opnået videregående udd.", "value": 'high'},
                ],
                value='all',
                id="income-education-selector",
            ),
        ], width=2),
        dbc.Col([
            dbc.Label('År:'),
            html.Div(
                dbc.Select(
                    id='income-year-selector',
                    options=[{'label': y, 'value': y} for y in df['year'].unique()],
                    value=2018,
                )
            ),
            html.Div([
                dbc.Button(
                    'Nulstil tidsserie',
                    id='income-clear-memory-button',
                    color='danger',
                    outline=True,
                    style={'marginBottom': '0.25em'}
                ),
                download_dropdown('income')]
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
    html.Div(dcc.Store(id='income-memory')), # reverts to default on every page refresh
    html.Div(dcc.Store(id='income-color-memory')), # reverts to default on every page refresh
    html.Div([dbc.Fade(
        controls, id='income-control-fade', is_in=False, style={"transition": "opacity 200ms ease"}
    )
    ], id='income-control-panel', className='control_panel'),
    html.Div(
        dbc.Container([html.H4(id='income-title', style={'textAlign': 'center'}), html.H5(id='income-subtitle', style={'textAlign': 'center'})], fluid=True), id='income-title-div', style={'paddingBottom': '0.25em'}
    ),
    html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Container([
                    dcc.Loading(
                        type='circle',
                        children=[
                            dcc.Graph(
                                id='income-map-graph',
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
                                id='income-line-graph',
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
    [Output('income-control-panel', 'style'),
     Output('income-control-fade', 'is_in')],
    [Input('button-filtre', 'n_clicks')],
    [State('url', 'pathname')]
)
def show_hide_panel(clicks, pathname):
    if pathname == '/income':
        if clicks == None:
            return [{'display': 'none'}, False]
        elif clicks % 2 == 0:
            return [{'display': 'none'}, False]
        else:
            return [{'display': 'block'}, True]
    else:
        raise PreventUpdate

@app.callback(
    [Output("button-income", "style"),
     Output("icon-income", "src")],
    [Input("url", "pathname")],
)
def set_active_button(pathname):
    if pathname == "/income":
        return [{'backgroundColor':RF_orange, 'borderColor': RF_orange, 'color': 'rgb(255, 255, 255)'}, 'data:image/svg+xml;base64,{}'.format(income_icon_active.decode())]
    else:
        return [{'backgroundColor':'rgb(255,255,255)', 'borderColor': 'rgb(51,51,51)', 'color': 'rgb(51,51,51)'}, 'data:image/svg+xml;base64,{}'.format(income_icon.decode())]

@app.callback(
    [Output('income-measure-selector', 'options'),
     Output('income-measure-selector', 'value')],
    [Input('income-variable-selector', 'value')],
    [State('income-measure-selector', 'value')]
)
def disable_measure(var, stt):
    if var == 'loenmv' and stt.startswith('p'):
        return [
            {'label': labels_dict['Gini'], 'value': 'Gini'},
            {'label': labels_dict['Theil_L'], 'value': 'Theil_L'},
            {'label': labels_dict['Theil_T'], 'value': 'Theil_T'},
            {'label': labels_dict['mean'], 'value': 'mean'},
            {'label': labels_dict['diff_gender'], 'value': 'diff_gender'},
            {'label': labels_dict['diff_heritage'], 'value': 'diff_heritage'},
            {'label': labels_dict['diff_labor'], 'value': 'diff_labor'},
            {'label': labels_dict['diff_education'], 'value': 'diff_education'},
            {'label':'Palma', 'value':None, 'disabled':True},
            {'label': labels_dict['p90p10'], 'value': 'p90p10', 'disabled':True},
            {'label': labels_dict['p90p50'], 'value': 'p90p50', 'disabled':True},
            {'label': labels_dict['p50p10'], 'value': 'p50p10', 'disabled':True},
        ], 'Gini'

    elif var == 'loenmv':
        return [
            {'label': labels_dict['Gini'], 'value': 'Gini'},
            {'label': labels_dict['Theil_L'], 'value': 'Theil_L'},
            {'label': labels_dict['Theil_T'], 'value': 'Theil_T'},
            {'label': labels_dict['mean'], 'value': 'mean'},
            {'label': labels_dict['diff_gender'], 'value': 'diff_gender'},
            {'label': labels_dict['diff_heritage'], 'value': 'diff_heritage'},
            {'label': labels_dict['diff_labor'], 'value': 'diff_labor'},
            {'label': labels_dict['diff_education'], 'value': 'diff_education'},
            {'label':'Palma', 'value':None, 'disabled':True},
            {'label': labels_dict['p90p10'], 'value': 'p90p10', 'disabled':True},
            {'label': labels_dict['p90p50'], 'value': 'p90p50', 'disabled':True},
            {'label': labels_dict['p50p10'], 'value': 'p50p10', 'disabled':True},
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
            {'label':'Palma', 'value':None, 'disabled':True},
            {'label': labels_dict['p90p10'], 'value': 'p90p10'},
            {'label': labels_dict['p90p50'], 'value': 'p90p50'},
            {'label': labels_dict['p50p10'], 'value': 'p50p10'},
        ], stt
@app.callback(
    [Output('income-title', 'children'),
     Output('income-subtitle', 'children')],
    [Input('income-variable-selector', 'value'),
    Input('income-measure-selector', 'value'),
    Input('income-gender-selector', 'value'),
    Input('income-age-selector', 'value'),
    Input('income-heritage-selector', 'value'),
    Input('income-education-selector', 'value'),
    Input('income-labor-selector', 'value'),
    Input('income-year-selector', 'value')]
)
def update_title(selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, selected_year):
    if selected_measure == 'Gini' or selected_measure.startswith('Theil') or selected_measure[1].isdigit():
        header = f'Figurerne viser ulighed i {labels_dict[selected_variable].lower()} målt ved {labels_dict[selected_measure]}'
    elif selected_measure == 'mean':
        header = f'Figurerne viser udvikling i gennemsnitlig {labels_dict[selected_variable].lower()}'
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
    if selected_age != 'all' and selected_gender == selected_heritage == 'all':
        txt_a = f'befolkningen mellem {labels_dict[selected_age]} år'
    elif selected_age != 'all':
        txt_a = f' mellem {labels_dict[selected_age]} år'
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
        Output(f'income-help-text{i}', 'is_open'),
        [Input(f'income-open-help{i}', 'n_clicks'),
         Input(f'income-close-help{i}', 'n_clicks')],
        [State(f'income-help-text{i}', 'is_open')]
    )
    def open_help_text(c1, c2, is_open):
        if c1 or c2:
            return not is_open
        else:
            return is_open

@app.callback(
    [Output('income-help-header0', 'children'),
     Output('income-help-body0', 'children')],
    [Input('income-variable-selector', 'value')]
)
def txt_help_button0(var):
    income_help_labels0 = {
        'aekvivadisp': html.P(['Dette indkomstmål registrerer familieindkomst for en given person efter skat og overførselsindkomster. Indkomstmålet er ”ækvivaleret”, hvilket vil sige, at der tages højde for antallet af personer i familien og deres alderssammensætning. Dette gøres på grund af stordriftsfordele: det er dyrere at være fire personer i en familie end at være to personer, men det er mindre end dobbelt så dyrt. Dette indkomstmål er det, som kommer tættest, blandt registrerede indkomstopgørelser, på at måle individers forbrugs- og opsparingsmulighed.', html.Br(), html.Br(), 'Indkomsten er angivet i 2015-kroner.', html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/personindkomst/aekvivadisp-13', target='_blank'),'.']),

        'dispon': html.P(['Dette indkomstmål registrerer individets disponible indkomst, dvs. inklusiv alle overførselsindkomster og fratrukket skat. Et individs disponible indkomst måler den indkomst, som personen har til rådighed til forbrug og opsparing.', html.Br(), html.Br(), 'Indkomsten er angivet i 2015-kroner.', html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/personindkomst/dispon-13', target='_blank'),'.']),

        'perindkialt': html.P(['Dette indkomstmål registrerer individets samlede indkomst (inklusiv fx overførselsindkomster, kapitalindkomster og private pensioner, men eksklusiv beregnet lejeværdi af egen bolig) før skat.', html.Br(), html.Br(), 'Indkomsten er angivet i 2015-kroner.', html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/personindkomst/perindkialt-13', target='_blank'),'.']),

        'loenmv': html.P(['Dette indkomstmål registrerer individets lønindkomst, inkl. bl.a. frynsegoder, fratrædelsesgodtgørelse og aktieoptioner. Lønindkomsten er målt før skat.', html.Br(), html.Br(), 'Indkomsten er angivet i 2015-kroner.', html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/personindkomst/loenmv-13', target='_blank'),'.']),
    }
    return labels_dict[var], income_help_labels0[var]

@app.callback(
    [Output('income-help-header1', 'children'),
     Output('income-help-body1', 'children')],
    [Input('income-measure-selector', 'value')]
)
def txt_help_button1(val):
    income_help_labels1 = {
        'Gini': html.P(["Dette mål for ulighed er et af de mest udbredte og angiver i hvilken grad indkomster er koncentreret hos en lille gruppe eller jævnt fordelt. En højere Gini-koefficient betyder mere ulighed: hvis alles indkomster er præcist det samme, er Gini-koefficienten 0, og hvis hele indkomsten ligger hos én enkelt person, er Gini-koefficienten 1.", html.Br(), html.Br(), "Læs mere ", html.A('her', href='https://da.wikipedia.org/wiki/Gini-koefficient', target='_blank'), ' og ', html.A('her', href='https://denstoredanske.lex.dk/gini-koefficient', target='_blank'), '.']),

        'Theil_L': html.P(["Dette mål for ulighed angiver i hvilken grad indkomster er koncentreret hos en lille gruppe eller jævnt fordelt. Et højere Theil-index angiver mere ulighed, og et Theil-index på 0 betyder, at alle har præcis den samme indkomst.", html.Br(), html.Br(), 'I forhold til Theils T-index er Theils L mere følsom overfor lave indkomster, dvs. at de tillægges mere vægt, når man udregner uligheden. Theils L er også kendt som ”mean log deviation”. Begge mål er særtilfælde af det generaliserede entropi-indeks.', html.Br(), html.Br(), "Læs mere om Theils L og Theils T ", html.A('her', href='https://en.wikipedia.org/wiki/Theil_index#:~:text=Derivation%20from%20entropy%20%20%20%20Notation%20,income%20in%20population%20%202%20more%20rows%20', target='_blank'),'.']),

        'Theil_T': html.P(["Dette mål for ulighed angiver i hvilken grad, indkomster er koncentreret hos en lille gruppe eller jævnt fordelt. Et højere Theil-index angiver mere ulighed, og et Theil-index på 0 betyder, at alle har præcis den samme indkomst.", html.Br(), html.Br(), 'I forhold til Theils L-index er Theils T mere følsom overfor højere indkomster, dvs. at de tillægges mere vægt, når man udregner uligheden. Både Thiels T og Theils L er særtilfælde af det såkaldte generaliserede entropi-indeks.', html.Br(), html.Br(), "Læs mere om Theils L og Theils T ", html.A('her', href='https://en.wikipedia.org/wiki/Theil_index#:~:text=Derivation%20from%20entropy%20%20%20%20Notation%20,income%20in%20population%20%202%20more%20rows%20', target='_blank'),'.']),

        'mean': html.P(["Dette mål angiver ikke ulighed i sig selv, men opgør gennemsnitlig indkomst. Målet er udregnet som et simpelt gennemsnit af det valgte indkomstmål for den pågældende gruppe og inden for hver enkelt kommune."]),

        'diff_gender': html.P(["Dette mål opgør indkomstforskellen mellem mænd og kvinder. Målet er udregnet ved at trække kvinders indkomst fra mænds, og en positiv værdi betyder således, at mænd i gennemsnit tjener mere end kvinder."]),

        'diff_heritage': html.P(["Dette mål opgør indkomstforskellen mellem danskere og indvandrere/efterkommere. Målet er udregnet ved at trække indvandrere og efterkommeres indkomst fra danskeres, og en positiv værdi betyder således, at danskere i gennemsnit tjener mere end indvandrere eller efterkommere."]),

        'diff_labor': html.P(["Dette mål opgør indkomstforskellen mellem personer med og uden højere uddannelse end grundskolen. Målet er udregnet ved at trække indkomsten for personer uden højere uddannelse end grundskolen fra indkomsten for personer med højere uddannelse end grundskolen. En positiv værdi betyder således, at en person med højere uddannelse end grundskolen i gennemsnit tjener mere end en person uden."]),

        'diff_education': html.P(["Dette mål opgør indkomstforskellen mellem personer med og uden videregående uddannelse. Målet er udregnet ved at trække indkomsten for personer uden videregående uddannelse fra indkomsten for personer med videregående uddannelse, og en positiv værdi betyder således, at personer med videregående uddannelser i gennemsnit tjener mere end personer uden."]),

        'p90p10': html.P(["For at udregne dette ulighedsmål, beregnes først 90%-percentilen, dvs. det indkomstniveau, man skal overstige for at være blandt de 10 %, som tjener mest. Dernæst beregnes 10%-percentilen, dvs. det indkomstniveau, man lige præcis skal overstige for ikke at være blandt de 10 % med de laveste indkomster. P90/P10 udregnes ved at dividere 90%-percentilen med 10%-percentilen. For eksempel betyder en P90/P10 på 5 at en person med en indkomst svarende til 90%-percentilen tjener 5 gange så meget som en person med en indkomst svarende til 10%-percentilen."]),

        'p90p50': html.P(["For at udregne dette ulighedsmål, beregnes først 90%-percentilen, dvs. det indkomstniveau, man skal overstige for at være blandt de 10 %, som tjener mest. Dernæst beregnes 50%-percentilen, også kendt som medianen, dvs. det indkomstniveau, man lige præcis skal overstige for at være blandt de 50 % med de højeste indkomster. P90/P50 udregnes ved at dividere 90%-percentilen med 50%-percentilen. For eksempel betyder en P90/P50 på 3 at en person med en indkomst svarende til 90%-percentilen tjener 3 gange så meget som en person med en indkomst svarende til 50%-percentilen."]),

        'p50p10': html.P(["For at udregne dette ulighedsmål, beregnes først 50%-percentilen, også kendt som medianen, dvs. det indkomstniveau, man lige præcis skal overstige for at være blandt de 50 % med de højeste indkomster. Dernæst beregner vi 10%-percentilen, dvs. det indkomstniveau, man lige præcis skal overstige for ikke at være blandt de 10 % med de laveste indkomster. P50/P10 udregnes ved at dividere 50%-percentilen med 10%-percentilen. For eksempel betyder en P50/P10 på 3 at en person med en indkomst svarende til 50%-percentilen tjener 3 gange så meget som en person med en indkomst svarende til 10%-percentilen."]),
    }
    return labels_dict[val], income_help_labels1[val]

@app.callback(
    [Output('income-help-header2', 'children'),
     Output('income-help-body2', 'children')],
     [Input('income-gender-selector', 'value')]
)
def txt_help_button2(_):
    return 'Køn', html.P(["Information om køn er baseret på CPR-nummers sidste ciffer.", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/TilSalg/Forskningsservice/Dokumentation/hoejkvalitetsvariable/folketal/koen', target='_blank'),'.'])

@app.callback(
    [Output('income-help-header3', 'children'),
     Output('income-help-body3', 'children')],
     [Input('income-heritage-selector', 'value')]
)
def txt_help_button3(_):
    return 'Herkomst', html.P(["Indvandrere er defineret som personer, der er født i udlandet og hvor ingen af forældrene er både danske statsborgere og født i Danmark. Efterkommere er personer, som er født i Danmark og hvor ingen af forældrene er både danske statsborgere og født i Danmark. Danskerne udgør resten af befolkningen.", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/TilSalg/Forskningsservice/Dokumentation/hoejkvalitetsvariable/udlaendinge/ie-type', target='_blank'),'.'])

@app.callback(
    [Output('income-help-header4', 'children'),
     Output('income-help-body4', 'children')],
     [Input('income-labor-selector', 'value')]
)
def txt_help_button4(_):
    return 'Opnået højere uddannelse end grundskole?', html.P(["Angiver om personen har fuldført anden uddannelse end grundskole og forberedende uddannelser. Påbegyndte, uafsluttede uddannelser tæller ikke med, kun fuldførte uddannelser.", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/uddannelsesdata/befolkningens-uddannelse', target='_blank'),'.'])

@app.callback(
    [Output('income-help-header5', 'children'),
     Output('income-help-body5', 'children')],
     [Input('income-labor-selector', 'value')]
)
def txt_help_button5(_):
    return 'Opnået videregående uddannelse?', html.P(["Videregående uddannelser inkluderer både korte videregående uddannelser (KVU, fx pædagog), mellemlange videregående uddannelser (MVU, fx skolelærer), lange videregående uddannelser (LVU, fx læge) og forskeruddannelser (ph.d.).", html.Br(), html.Br(), "Dokumentation hos Danmarks Statistik findes ", html.A('her', href='https://www.dst.dk/da/Statistik/dokumentation/Times/uddannelsesdata/befolkningens-uddannelse', target='_blank'),'.'])

@app.callback(
    Output('income-education-selector', 'value'),
    [Input('income-measure-selector', 'value'),
    Input('income-labor-selector', 'value')]
)
def education_correction(msr, lab):
    if msr == 'diff_labor' or msr == 'diff_education':
        return 'all'
    elif lab == 'unskilled':
        return 'low'
    else:
        raise PreventUpdate

@app.callback(
    [Output('income-heritage-selector', 'value'),
    Output('income-heritage-selector', 'options')],
    [Input('income-measure-selector', 'value')],
    [State('income-heritage-selector', 'value')]
)
def disable_heritage(msr, state):
    if msr == 'diff_heritage':
        return 'all', [
            {"label": "Alle", "value": "all"},
            {"label": "Dansk", "value": 'danish', 'disabled':True},
            {"label": "Indvandrere og efterkommere", "value": 'nondanishnonwestern', 'disabled':True},
            {"label": "Ikke-vestlige indvandrere og efterkommere", "value": 'nonwestern', 'disabled':True},
            ]
    else:
        return state, [
            {"label": "Alle", "value": "all"},
            {"label": "Dansk", "value": 'danish'},
            {"label": "Indvandrere og efterkommere", "value": 'nondanishnonwestern'},
            {"label": "Ikke-vestlige indvandrere og efterkommere", "value": 'nonwestern'},
            ]

@app.callback(
    [Output('income-gender-selector', 'value'),
    Output('income-gender-selector', 'options')],
    [Input('income-measure-selector', 'value')],
    [State('income-gender-selector', 'value')]
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
    Output('income-education-selector', 'options'),
    [Input('income-labor-selector', 'value'),
     Input('income-measure-selector', 'value')],
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
    [Output('income-labor-selector', 'options'),
     Output('income-labor-selector', 'value')],
    [Input('income-education-selector', 'value'),
     Input('income-measure-selector', 'value')],
    [State('income-labor-selector', 'value')]
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
    [Output('income-memory', 'clear_data'),
     Output('income-color-memory', 'clear_data')],
    [Input('income-clear-memory-button', 'n_clicks')]
)
def erase_memory(click):
    if click is None:
        raise PreventUpdate
    else:
        return True, True

@app.callback(
    Output('income-color-memory', 'data'),
    [Input('income-map-graph', 'clickData')],
    [State('income-color-memory', 'data')]
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
    Output('income-memory', 'data'),
    [Input('income-map-graph', 'clickData')],
    [State('income-memory', 'data')]
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

##### Begin plotting graphs #####

# @app.callback(
#     Output('income-map-graph', 'figure'),
#     [Input('income-map-graph', 'hoverData')],
#     [State('income-map-graph', 'figure')]
# )
# def display_hover_data(hoverData, fig):
#     ### NOTE:  cannot have multiple output for same id property. Including in the definition of the figure does not work
#     if hoverData is None:
#         raise PreventUpdate
#     else:
#         l, x, y = get_coordinates(
#             kom = komstr2koder[hoverData['points'][0]['customdata'][0]],
#             d = district_lookup
#         )
#
#         if l > 1:
#             for i in range(l):
#                 line = px.line_geo(lat=y[i], lon=x[i], projection='mercator',  color_discrete_sequence=['rgb(0,0,0)']*len(x))
#                 line.data[0].showlegend=False
#                 line.update_traces(
#                    hovertemplate=None,
#                    hoverinfo='skip'
#                 )
#                 fig.add_trace(line.data[0])
#         else:
#             raise PreventUpdate
#     return fig

@app.callback(
    Output('income-map-graph', 'figure'),
    [Input('income-variable-selector', 'value'),
    Input('income-measure-selector', 'value'),
    Input('income-gender-selector', 'value'),
    Input('income-age-selector', 'value'),
    Input('income-heritage-selector', 'value'),
    Input('income-education-selector', 'value'),
    Input('income-labor-selector', 'value'),
    Input('income-year-selector', 'value')]
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
                            labels={selected_measure: 'DKK'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.0f}<br>" +\
                "Antal uden videregående udd.: %{customdata[2]:,}<br>" +\
                "Antal med videregående udd.: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at dem med videregående uddannelse har en højere indkomst)'
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
                            labels={selected_measure: 'DKK'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.0f}<br>" +\
                "Antal m. grundskole som højest fuldførte udd.: %{customdata[2]:,}<br>" +\
                "Antal m. højere udd. end grundskole: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at dem m. højere udd. end grundskole har en højere indkomst)'
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
                            labels={selected_measure: 'DKK'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.0f}<br>" +\
                "Antal kvinder: %{customdata[2]:,}<br>" +\
                "Antal mænd: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at mænd har en højere indkomst)'
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
                            labels={selected_measure: 'DKK'},
                            color_continuous_midpoint=0
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], grp1['observations'], grp2['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.0f}<br>" +\
                "Antal danskere: %{customdata[2]:,}<br>" +\
                "Antal ikke-vestlige indvandrere og efterkommere: %{customdata[3]:,}<br>"
            )
        )
        anno_text2 = '(Rød indikerer, at danskere har en højere indkomst)'
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
                            labels={selected_measure: 'DKK'},
                            # color_continuous_midpoint=np.median(dfs[selected_measure]),
                           )
        fig.update_traces(
            customdata= np.stack((dfs['municipality'], dfs[selected_measure], dfs['observations']), axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"+\
                "Værdi: %{customdata[1]:,.0f}<br>" +\
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
                "Værdi: %{customdata[1]:,.0f}<br>" +\
                "Antal observationer: %{customdata[2]:,}"
            )
        )

    fig.update_geos(fitbounds="locations", visible=False)
    if selected_measure == 'mean' or selected_measure.startswith('diff'):
        fig.update_layout(
            coloraxis_colorbar_tickformat=',.000',
        )
    else:
        fig.update_layout(
            coloraxis_colorbar_tickformat='',
        )
    fig.update_layout(
        font_family='Avenir Next',
        margin={"r":0,"t":0,"l":0,"b":0},
        font_size=12,
        # coloraxis_colorbar_tickformat=',.000',
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
    Output('income-line-graph', 'figure'),
    [
    Input('income-variable-selector', 'value'),
    Input('income-measure-selector', 'value'),
    Input('income-gender-selector', 'value'),
    Input('income-age-selector', 'value'),
    Input('income-heritage-selector', 'value'),
    Input('income-education-selector', 'value'),
    Input('income-labor-selector', 'value'),
    Input('income-memory', 'data'),
    Input('income-color-memory', 'data'),
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
                                    '%{y:,.0f} <br>'+
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
                    '%{y:,.0f} <br>'+
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
                                    '%{y:,.0f} <br>'+
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
                    '%{y:,.0f} <br>'+
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
                                    '%{y:,.0f} <br>'+
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
                    '%{y:,.0f} <br>'+
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
                                    '%{y:,.0f} <br>'+
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
                    '%{y:,.0f} <br>'+
                    '%{text}'
                    "<extra></extra>"
                ))
    elif selected_measure == 'Gini' or selected_measure == 'Theil_L' or selected_measure == 'Theil_T' or selected_measure[1].isdigit():
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
    else:
        fig.add_trace(go.Scatter(x=df['year'].unique(), y=line_all[selected_measure], name='Hele Danmark',
                                mode='lines', line=dict(color=hele_danmark_color), meta=line_all['observations'],
                                hovertemplate=
                                '<b>Hele Danmark</b><br>'+
                                '%{x}: '+
                                '%{y:,.0f} <br>'+
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
                '%{y:,.0f} <br>'+
                'Antal observationer: %{meta:,}'
                "<extra></extra>"))
    if selected_measure == 'mean' or selected_measure.startswith('diff'):
        fig.update_layout(
            yaxis_title='DKK',
            yaxis_tickformat=',.000',
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
    Output('income-download-csv-map', 'href'),
    [Input('income-download-csv-map-button', 'n_clicks'),
     Input('income-variable-selector', 'value'),
     Input('income-measure-selector', 'value'),
     Input('income-gender-selector', 'value'),
     Input('income-age-selector', 'value'),
     Input('income-heritage-selector', 'value'),
     Input('income-education-selector', 'value'),
     Input('income-labor-selector', 'value'),
     Input('income-year-selector', 'value')]
)
def link_download_map(click, selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, selected_year):
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
    return f"/downloadMap?{query_string}" # /dash/urlToDownload?

@app.server.route('/downloadMap') # /dash/urlToDownload?
def download_map_csv():
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
    Output('income-download-csv-series', 'href'),
    [Input('income-download-csv-series-button', 'n_clicks'),
     Input('income-variable-selector', 'value'),
     Input('income-measure-selector', 'value'),
     Input('income-gender-selector', 'value'),
     Input('income-age-selector', 'value'),
     Input('income-heritage-selector', 'value'),
     Input('income-education-selector', 'value'),
     Input('income-labor-selector', 'value'),
     Input('income-memory', 'data')]
)
def link_download_series(click, selected_variable, selected_measure, selected_gender, selected_age, selected_heritage, selected_education, selected_labor, municipalities):
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
    return f"/downloadSeries?{query_string}" # /dash/urlToDownload?

@app.server.route('/downloadSeries') # /dash/urlToDownload?
def download_series_csv():
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
    Output('income-download-png-series', 'href'),
    [Input('income-download-png-series-button', 'n_clicks'),
     Input('income-line-graph', 'figure')]
 )
def link_download_series_image(click, fig):
    if fig is None:
        raise PreventUpdate
    else:
        img_bytes = plotly.io.to_image(fig, format='png', engine='kaleido') # img as bytes
        out = base64.b64encode(img_bytes) # encoded
        query_param = {'encoding': out}
        query_string = urllib.parse.urlencode(query_param, doseq=True)
        return f"/downloadSeriesImg?{query_string}"

@app.server.route('/downloadSeriesImg')
def download_series_img():
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
    Output('income-download-png-map', 'href'),
    [Input('income-download-png-map-button', 'n_clicks'),
     Input('income-map-graph', 'figure')]
 )
def link_download_map_image(click, fig):
    if fig is None:
        raise PreventUpdate
    else:
        img_bytes = plotly.io.to_image(fig, format='png', engine='kaleido') # img as bytes
        out = base64.b64encode(img_bytes) # encoded
        query_param = {'encoding': out}
        query_string = urllib.parse.urlencode(query_param, doseq=True)
        return f"/downloadMapImg?{query_string}"

@app.server.route('/downloadMapImg')
def download_map_img():
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



# help(dbc.Label())
# help(dbc.DropdownMenu())
# px.colors.sequential.RdBu_r
