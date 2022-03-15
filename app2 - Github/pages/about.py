import os
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import flask
import base64

from ineq_app import app
from utils import encode_svg, path2file
from utils import top_banner

server = app.server

three_icons = html.Div(id='id-frontpage-three-icons', children=[dbc.Row([
    dbc.Col([
        html.A(
            html.Img(id='icon-frontpage-income', src='data:image/svg+xml;base64,{}'.format(encode_svg('ikoner_forside_01.svg').decode()), className='class-frontpage-three-icons'),
            href="/income",
        ),
    ]),
    dbc.Col([
        html.A(
            html.Img(id='icon-frontpage-sundhed', src='data:image/svg+xml;base64,{}'.format(encode_svg('ikoner_forside_02.svg').decode()), className='class-frontpage-three-icons'),
            href="/health",
        )
    ]),
    dbc.Col([
        html.A(
            html.Img(id='icon-frontpage-education', src='data:image/svg+xml;base64,{}'.format(encode_svg('ikoner_forside_03.svg').decode()), className='class-frontpage-three-icons'),
            href="/education",
        )
    ]),
])])

layout = html.Div(id='id-frontpage', children=[
    html.Div([top_banner()]),
    dbc.Row([dbc.Container(
        html.H3(['Velkommen'],
        style={'textAlign': 'center', 'color': 'rgb(255,255,255)', 'paddingTop': '2rem', 'paddingBottom':'1rem'})
    )]),
    dbc.Row([dbc.Container(
        html.H4(id='id-frontpage-text-two', children=['Med denne app kan du undersøge ligheden og uligheden i Danmark inden for områderne indkomst, sundhed og uddannelse. Du kan afgrænse dine søgekriterier og interagere med både danmarkskort og grafer.'])
    )]),
    dbc.Row([
        dbc.Button('Klik her for introduktion', id='id-frontpage-button-intro', className='btn shadow-none', color='warning'),
        # html.Video(
        #     # autoPlay=True,
        #     controls=True,
        #     src=path2file('/static/intro1920x1080.mp4')
        # ),
        dbc.Modal(id='id-frontpage-modal', size='lg', children=[
            dbc.ModalBody(id='id-frontpage-modal-body', children=[
                # html.Video(
                #     # autoPlay=True,
                #     controls=True,
                #     src=path2file('intro1920x1080.mp4')
                # )
            ]),
            dbc.ModalFooter(dbc.Button("Luk", id='id-frontpage-modal-close'))
        ])
    ]),
    dbc.Row([dbc.Container(three_icons)])
])

@app.callback(
    Output('id-frontpage-modal', 'is_open'),
    [Input('id-frontpage-button-intro', 'n_clicks'),
     Input('id-frontpage-modal-close', 'n_clicks')],
    [State('id-frontpage-modal', 'is_open')]
)
def open_intro_video(c1, c2, is_open):
    if c1 or c2:
        return not is_open
    else:
        return is_open

# @server.route('/static/<path:path>')
# def serve_static(path):
#     root_dir = os.path.dirname(__file__)
#     return flask.send_from_directory(os.path.join(root_dir, 'static'), path)
