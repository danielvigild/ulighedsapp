import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import base64

### import from directories ###
from ineq_app import app
from utils import (
    RF_orange,
    encode_svg
)
from pages import (
    about,
    income,
    health,
    education,
    documentation,
)

# NOTE: dash-bootstrap-components==0.10.6

income_icon = encode_svg('inc_dark.svg')
income_icon_active = encode_svg('inc_orange.svg')
edu_icon = encode_svg('edu_dark.svg')
edu_icon_active = encode_svg('edu_orange.svg')

# Describe the layout/ UI of the app
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content"),
    ]
)

# Update page
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname == "/income":
        return income.layout
    elif pathname == "/health":
        return health.layout
    elif pathname == '/education':
        return education.layout
    elif pathname == '/pages/about':
        return about.layout
    elif pathname == '/pages/documentation':
        return documentation.layout
    else:
        return about.layout

@app.callback(
    Output('id-guide', 'style'),
    [Input('guide-button', 'n_clicks')]
)
def show_hide_guide(clicks):
    if clicks == None:
        return {'display': 'none'}
    elif clicks % 2 == 0:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

# @app.callback(
#      Output('icon-filtre', 'src'),
#     [Input('button-filtre', 'n_clicks')],
#     [State('url', 'pathname')]
# )
# def show_hide_panel(clicks, pathname):
#     if pathname == '/income':
#         if clicks == None:
#             return [{'display': 'none'}, False, 'data:image/svg+xml;base64,{}'.format(encode_svg('filter_dark.svg').decode())]
#         elif clicks % 2 == 0:
#             return [{'display': 'none'}, False, 'data:image/svg+xml;base64,{}'.format(encode_svg('filter_dark.svg').decode())]
#         else:
#             return [{'display': 'block'}, True, 'data:image/svg+xml;base64,{}'.format(encode_svg('filter_down_dark.svg').decode())]
#     else:
#         raise PreventUpdate

if __name__ == "__main__":
    # app.run_server(debug=False, host='0.0.0.0')
    app.run_server(debug=False)
