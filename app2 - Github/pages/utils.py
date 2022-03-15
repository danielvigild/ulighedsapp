import os
import dash_html_components as html
# import dash_core_components as dcc
import dash_bootstrap_components as dbc
import base64

RF_orange = 'rgb(242,146,12)'
RF_gray = 'rgb(244,246,248)'

def get_highlights(selection, geojson, district_lookup):
    """
    For selecting a single municipality. Returns geojson for only selection
    Args:
        selection: KOMKODE (int)
        geojson: geojson
        district_lookup: KOMKODE as key and coordinates as value (dict)
    """
    geojson_highlights = dict()
    for k in geojson.keys():
        if k != 'features':
            geojson_highlights[k] = geojson[k]
        else:
            geojson_highlights[k] = district_lookup[selection]
    return geojson_highlights

def get_coordinates(kom, d):
    length = len(d[kom]['geometry']['coordinates'])
    ddict = d[kom]
    x = []
    y = []
    if length > 1:
        for i in range(length):
            _x = [v[0] for v in ddict['geometry']['coordinates'][i][0]]
            x.append(_x)
            _y = [v[1] for v in ddict['geometry']['coordinates'][i][0]]
            y.append(_y)
            return length, x, y
    else:
        x = [v[0] for v in ddict['geometry']['coordinates'][0]]
        y = [v[1] for v in ddict['geometry']['coordinates'][0]]
        return length, x, y

def path2file(fname: str) -> str:
    """
    Returns path relative to current work directory.
    Arg:
        dataset: file name, e.g. 'income.csv'
    """
    script_dir = os.path.dirname(__file__) # the cwd relative path of the script file
    type_dir = 'files' # dir of target file
    return os.path.join(script_dir, type_dir, fname) # the cwd-relative path of the target file

def download_dropdown(page: str):
    """
    Returns a dropdown menu component for downloading data and graphs.
    Arg:
        page: name of page, e.g. 'income'
    """
    return dbc.DropdownMenu([
        dbc.DropdownMenuItem('Download data (CSV)', header=True),
        html.A(dbc.DropdownMenuItem('Kommunekort', id=page+'-download-csv-map-button'), id=page+'-download-csv-map'),
        html.A(dbc.DropdownMenuItem('Tidsserie', id=page+'-download-csv-series-button'), id=page+'-download-csv-series'),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem('Download graf (PNG)', header=True),
        html.A(dbc.DropdownMenuItem('Kommunekort', id=page+'-download-png-map-button'), id=page+'-download-png-map'),
        html.A(dbc.DropdownMenuItem('Tidsserie', id=page+'-download-png-series-button'), id=page+'-download-png-series'),
        # dbc.DropdownMenuItem(divider=True),
        # dbc.DropdownMenuItem('Download skærmbillede (PDF)', header=True),
        # dbc.DropdownMenuItem('Snapshot'),
    ], label='Gem', right=True, group=True, id=page+'-download-button', className='shadow-none', toggle_style={'backgroundColor':'rgb(255,255,255)', 'borderColor': 'rgb(218, 223, 227)', 'color': '#495057', 'fontWeight': 'bold', 'maxWidth':'none', 'width': '100%'})

def button_help(page: str, no: str):
    """
    Returns Div w/ badge and modal for information
    Arg:
        page: name of page, e.g. 'income'
        no: for numbering the ID, e.g. '0'
    """
    return html.Div([
        dbc.Badge('?', id=page+'-open-help'+no), # href='javascript:;' : do nothing
        dbc.Modal([
            dbc.ModalHeader(id=page+'-help-header'+no),
            dbc.ModalBody(id=page+'-help-body'+no),
            dbc.ModalFooter(dbc.Button("Luk", id=page+"-close-help"+no)),
        ], id=page+"-help-text"+no, size='lg'),
    ], style={'marginLeft': 10, 'display': 'inline-block'})

def encode_svg(fname: str) -> str:
    """
    Returns encoding for guide page. Must be decoded.
    """
    file = path2file(fname)
    return base64.b64encode(open(file, 'rb').read())

def get_menu():
    menu = dbc.Nav([
        dbc.NavItem(dbc.Button('Indkomst', href="/income", outline=True, color='dark', id='button-income')),
        dbc.NavItem(dbc.Button('Sundhed', href="/pages/health", outline=True, color='dark', id='button-health')),
        dbc.NavItem(dbc.Button('Uddannelse', href="/pages/education", outline=True, color='dark', id='button_education')),
        dbc.NavItem(dbc.Button('Om siden', href="/pages/about", outline=True, color='secondary', id='button_front')),
        dbc.NavItem(dbc.Button('Dokumentation', href="/pages/documentation", outline=True, color='secondary', id='button_documentation')),
    ], justified=True, pills=True, style={'padding-top':1, 'padding-bottom':1})
    return menu

def navigation():
    return html.Div(dbc.Container(get_menu()), style={'backgroundColor':'orange'})

health_icon_file = r'C:\Users\JFL\Desktop\RFF\Inequality_in_many_dimensions\app\pages\icons\health_dark.svg'
health_icon = base64.b64encode(open(health_icon_file, 'rb').read())
education_icon_file = r'C:\Users\JFL\Desktop\RFF\Inequality_in_many_dimensions\app\pages\icons\edu_dark.svg'
education_icon = base64.b64encode(open(education_icon_file, 'rb').read())
documentation_icon_file = r'C:\Users\JFL\Desktop\RFF\Inequality_in_many_dimensions\app\pages\icons\doc_dark.svg'
documentation_icon = base64.b64encode(open(documentation_icon_file, 'rb').read())

def get_menu2():
    menu = dbc.Row([
        dbc.Col([
            dbc.Nav([
                dbc.NavItem([
                    html.Img(src='data:image/svg+xml;base64,{}'.format(encode_svg('filter_dark.svg').decode()), id='icon-filtre', style={'width': '50px', 'height': '1rem'}),
                    dbc.Button('Filtre', id='button-filtre', className='btn shadow-none')
                ])
            ], style={'paddingTop': '0.375rem'})
        ], width=2),
        dbc.Col([
            dbc.Nav([
                dbc.NavItem([
                    html.A(
                        html.Img(id='icon-income', src='data:image/svg+xml;base64,{}'.format(encode_svg('inc_dark.svg').decode()), style={'height': '2.2rem', 'verticalAlign': 'bottom', 'paddingRight': '0.2rem'}),
                        href="/income",
                    ),
                    dbc.Button('Indkomst', href="/income", outline=True, color='dark', id='button-income', className='btn shadow-none')
                ]),
                dbc.NavItem([
                    html.Img(src='data:image/svg+xml;base64,{}'.format(health_icon.decode()), style={'height': '2.2rem', 'verticalAlign': 'middle', 'paddingRight': '0.2rem'}),
                    dbc.Button('Sundhed', href="/health", outline=True, color='dark', id='button-health', className='btn shadow-none')
                ]),
                dbc.NavItem([
                    html.Img(src='data:image/svg+xml;base64,{}'.format(education_icon.decode()), style={'height': '2.2rem', 'verticalAlign': 'middle', 'paddingRight': '0.2rem'}),
                    dbc.Button('Uddannelse', href="/education", outline=True, color='dark', id='button_education', className='btn shadow-none')
                ]),
                dbc.NavItem([
                    html.Img(src='data:image/svg+xml;base64,{}'.format(documentation_icon.decode()), style={'height': '2.2rem', 'verticalAlign': 'bottom', 'paddingRight': '0.2rem'}),
                    dbc.Button('Dokumentation', href="/pages/documentation", outline=True, color='secondary', id='button_documentation', className='btn shadow-none'),
                ]),
            ], justified=True, pills=False)
        ], width=10)
    ], no_gutters=True)
    return menu

def navigation2():
    return html.Div(dbc.Container(get_menu2(), fluid=True), style={'backgroundColor': RF_gray, 'paddingTop':'0.5em', 'paddingBottom': '0.5em'})

logo_image = encode_svg('logo-full.svg')
guide_icon = encode_svg('guide_orange.svg')

def get_banner():
    banner = dbc.Row([
        dbc.Col([
            html.Div([
                html.A([
                    html.Img(
                        # src='data:image/svg+xml;utf8,catalogue-catalog.svg'
                        # src='data:image/svg;utf-8,logo-full.svg', width='250px'
                        src='data:image/svg+xml;base64,{}'.format(logo_image.decode()), width='100%'
                        )
                    ], href='https://www.rockwoolfonden.dk/', target='_blank')
            ], style={'textAlign': 'left', 'verticalAlign': 'bottom', 'paddingTop': '0.7em'})
        ], width=2),
        dbc.Col([
            html.H3(id='banner-header', children='UNDERSØG LIGHEDEN OG ULIGHEDEN I DANMARK', style={'textAlign': 'center', 'verticalAlign': 'bottom', 'paddingTop': '0.3em'})
        ], width=8),
        dbc.Col([
            html.Div([
                html.Div([
                    html.Img(src='data:image/svg+xml;base64,{}'.format(guide_icon.decode()), style={'height': '2.2rem', 'paddingRight': '0.2rem'}),
                ], style={'verticalAlign': 'bottom', 'display': 'inline-block'}),
                html.Div([
                    dbc.Button('Guide', id='guide-button', block=True)], style={'verticalAlign': 'middle', 'display': 'inline-block'}) #style={'backgroundColor': RF_orange, 'borderColor': RF_orange}),
                ],
            style={'paddingTop': '0.3em', 'textAlign': 'right', 'verticalAlign': 'bottom'})
        ], width=2)
    ])
    return banner

def top_banner():
    return html.Div(dbc.Container(get_banner(), fluid=True), id='top-banner', style={'backgroundColor': 'rgb(255,255,255)', 'paddingBottom': '0.5em', 'paddingTop':'0.25em'})

labels_dict = {
    'gp': 'Kontakt med almen læge',
    'copd': 'Kronisk Obstruktiv Lungesygdom (KOL)',
    't2diabetes': 'Type 2-diabetes',
    'age1': '30 og 39',
    'age2': '40 og 49',
    'age3': '50 og 59',
    'age4': '60 og 65',
    'health_age1': '18 og 29',
    'health_age2': '30 og 39',
    'health_age3': '40 og 49',
    'health_age4': '50 og 59',
    'health_age5': '60 år og derover',
    'admissions': 'Antal hospitalsindlæggelser',
    'nights': 'Antal dage indlagt på hospital',
    'hfpria': 'Måneders fuldført uddannelse',
    'labor': 'Ufaglært/Ikke-ufaglært',
    'education': 'Uddannelsesbaggrund',
    'aekvivadisp': 'Ækvivaleret disponibel indkomst',
    'dispon': 'Disponibel indkomst',
    'perindkialt': 'Samlet indkomt',
    'loenmv': 'Lønindkomst',
    'Gini': 'Gini-koefficient',
    'Theil_L': 'Theil-index (Theils L)',
    'Theil_T': 'Theil-index (Theils T)',
    'mean': 'Gennemsnit',
    'diff_gender': 'Forskel mht. køn',
    'diff_immdes': 'Forskel mht. herkomst',
    'diff_education': 'Forskel mht. opnået videregående udd. og ingen videregående udd.',
    'diff_labor': 'Forskel mht. højere udd. end grundskole og grundskole som højest fuldførte udd.',
    'man': 'mænd',
    'woman': 'kvinder',
    'mænd': 'mandlige',
    'kvinder': 'kvindelige',
    'all': 'alle',
    'danish': 'danskere',
    'danskere': 'danske',
    'nondanish': 'indvandrere og efterkommere',
    'skilled': 'højere udd. end grundskole',
    'unskilled': 'grundskole som højest fuldførte udd.',
    'low': 'ingen videregående udd.',
    'high': 'opnået videregående udd.',
    'p90p10': 'P90/P10',
    'p90p50': 'P90/P50',
    'p50p10': 'P50/P10',
}
