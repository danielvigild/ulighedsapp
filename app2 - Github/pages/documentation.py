import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

from ineq_app import app
from utils import navigation2

income_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P([
                'Population (separat for hvert år):', html.Br(),
                '- Personer i bef mlm 34 og 64, begge inklusive.', html.Br(),
                '- Valide svar på køn, etnicitet, bopæl, uddannelse og alle tre indkomstmål', html.Br(),
                '- Selvstændige sorteres fra (baseret på arbstil (1980-1993), nyarb (1994-1995), socstil_kode (1996-2007) og soc_status_kode (2008-) fra ras (fra 1990 og fra er pnr ikke unikt i ras, vi bruger, dem der har novprio == 1 eller prim == 1)).', html.Br(),
                html.Br(),
                'Databehandling:', html.Br(),
                '- Indkomster under 1 sættes til 1.', html.Br(),
                '- Alle indkomster inflationskorrigeret'
            ]
            , className="card-text"),
        ]
    ), className="mt-3"
)
health_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P([
                'Population (separat for hvert år):', html.Br(),
                '- Personer i bef, som er fyldt 18.', html.Br(),
                '- Valide svar på køn, etnicitet, bopæl og uddannelse og alle tre sundhedsmål.', html.Br(),
                '- Drop alle med pattype != 0.', html.Br(),
                '- Behold kun aktionsdiagnsen.', html.Br(),
                '- Drop alle indlæggelser og sengedage ifm. fødsel.', html.Br()
            ], className="card-text"),
        ]
    ), className="mt-3"
)
education_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("""

            """, className="card-text"),
        ]
    ), className="mt-3"
)

tabs = dbc.Tabs(
    [
        dbc.Tab(income_tab, label="Indkomst", id='income_tab'),
        dbc.Tab(health_tab, label="Sundhed", id='health_tab'),
        dbc.Tab(education_tab, label="Uddannelse", id='education_tab'),
    ], id='tabs'
)

layout = html.Div([
    html.Div([navigation2()]),

    html.Div(dbc.Container(tabs, fluid=True, style={'marginTop': 2}))
], style={'backgroundColor':'rgb(240, 240, 240)', 'height': '100vh' })

@app.callback(
    Output("button_documentation", "style"),
    [Input("url", "pathname")],
)
def set_active_button(pathname):
    if pathname == "/pages/documentation":
        return {'backgroundColor':'rgb(242, 146, 12)', 'borderColor': 'rgb(242, 146, 12)', 'color': 'rgb(255, 255, 255)'}
    else:
        return {'backgroundColor':'rgb(244, 246, 248)', 'borderColor': 'rgb(108, 117, 125)', 'color': 'rgb(51, 51, 51)'}
