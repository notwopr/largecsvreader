
"""
Title: Large CSV Viewer.
Author: David Choi
Date: Apr 27, 2023
"""
from dash import dcc, html, callback_context, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import dash
import base64
import io

external_stylesheets = [
    dbc.themes.MORPH,
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    "https://fonts.googleapis.com/css2?family=Fredoka&display=swap",
    "https://fonts.googleapis.com/css2?family=Bayon&display=swap",
    "https://fonts.googleapis.com/css2?family=Oswald:wght@500&display=swap",
    "https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap",
    "https://fonts.googleapis.com/css2?family=Sanchez&display=swap",
    "https://fonts.googleapis.com/css2?family=Inter:wght@200&display=swap"
    ]
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=external_stylesheets
    )


style_table={
        }
fixed_rows={
            'headers': True, 'data': 0,
        }
style_header={
            'fontWeight': 'bold',
            'font-family': 'Inter, sans-serif',
            'border': '1px solid rgb(40, 52, 66)',
        }
style_data={
            'font-family': 'Inter, sans-serif',
        }
style_cell={
            'padding': 2,
            'padding-right': 8,
        }

title_section = html.H1('TOO DAMN BIG CSV VIEWER', className='mt-3 fw-bold text-center')
description_section = html.H4("When you don\'t have Excel and your XLS/CSV file is too large for Google Sheets. :(", className='text-center')

table_section = html.Div(dash_table.DataTable(
    style_table=style_table,
    fixed_rows=fixed_rows,
    style_data=style_data,
    style_header=style_header,
    style_cell=style_cell,
    sort_action='native',
    sort_mode='single',
    filter_action='native',
    sort_by=[],
    id='csvchart',
), className='ps-3 pe-3')

input_section = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A(html.B('Select a File'))
        ]),
        style={
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
        },
        multiple=False,
        className='pe-3 ps-3 text-center'
    ),
    html.Div(id='output-data-upload'),
    html.Br(),
    dcc.Dropdown(
        id='whatcols',
        value=[],
        multi=True,
        placeholder='Select Columns You Want Displayed',
        clearable=False,
        searchable=False,
        # className='rounded-3 ms-2 me-2 mb-1 mt-1 w-auto',
        ),
    html.Div([
        html.B('Columns to Display: '),
        html.Span(id='displaycols'),
    ], id='showchoices'),
    html.Button(
        id='confirmcols',
        n_clicks=0,
        children='Submit',
        type='button',
        className='btn btn-outline-dark m-1 rounded-3'
        )
], className='ps-3 pe-3 pb-3')

app.layout = html.Div(
    [
        title_section,
        description_section,
        input_section,
        table_section,
    ], className='p-8'
)

# Instantiate Global File Storage
class CentralStorage:
    def __init__(self):
        self.sourcedf = pd.DataFrame(data=[])
central = CentralStorage()


def parse_contents(contents, filename, date):
    """parse XLS/CSV file"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')), low_memory=False)
            
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))

        # store to global variable to prevent file from loading everytime callback is made
        central.sourcedf = df

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ]), pd.DataFrame(data=[])

    return [html.B('File Uploaded: '), filename], df.columns.tolist()

@app.callback(
    Output('output-data-upload', 'children'),
    Output('whatcols', 'options'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    )
def update_output(contents, filename, last_modified):
    
    if contents is not None:
        children, colnames = parse_contents(contents, filename, last_modified)
        return children, colnames
    else:
        return html.B('No File Loaded.'), []


# gen chart
@app.callback(
    Output('csvchart', 'data'),
    Output('displaycols', 'children'),
    Output('csvchart', 'columns'),
    Input("confirmcols", 'n_clicks'),
    Input('whatcols', 'value'),
    Input('csvchart', 'data'),
    Input("csvchart", 'sort_by'),
    )
def gen_csvtable(n_clicks, confirmcols, csvchart, sort_by):
    if len(central.sourcedf)>0 and callback_context.triggered[0]['prop_id'].endswith('n_clicks'):
        newdf = central.sourcedf[confirmcols]
        csvchart = newdf.to_dict('records')
        columns = [{"name": i, 'id': i} for i in newdf.columns]
    elif csvchart and callback_context.triggered[0]['prop_id'].endswith('sort_by'):
        df = pd.DataFrame.from_records(csvchart)
        df = df.sort_values(
            by=sort_by[0]['column_id'],
            ascending=sort_by[0]['direction'] == 'asc',
            inplace=False
            )
        csvchart = df.to_dict('records')
        columns = [{"name": i, 'id': i} for i in df.columns]
    elif csvchart:
        
        df = pd.DataFrame.from_records(csvchart)
        columns = [{"name": i, 'id': i} for i in df.columns]
    else:
        df = pd.DataFrame(data=[])
        csvchart = df.to_dict('records')
        columns = [{"name": i, 'id': i} for i in df.columns]
    return csvchart, ', '.join(confirmcols), columns

if __name__ == '__main__':
    app.run_server(debug=False)
    
