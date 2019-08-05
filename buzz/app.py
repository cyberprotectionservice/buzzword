import argparse
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objects as go
import os
import sys

from buzz.corpus import Corpus
from buzz.dashview import MAPPING, CHART_TYPES, _make_component, PLOTTERS

LABELS = dict(
    w="Word",
    l="Lemma",
    g="Governor index",
    f="Dependency role",
    x="Wordclass",
    i="Token index",
    s="Sentence number",
    file="Filename",
    speaker="Speaker",
)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
ALL_DATA = dict(corpus=None)

def _parse_cmdline_args():
    """
    Command line argument parsing
    """
    parser = argparse.ArgumentParser(
        description="Run the buzzword app for a given corpus."
    )

    parser.add_argument(
        "-l",
        "--load",
        default=True,
        action="store_true",
        required=False,
        help="Load corpus into memory. Longer startup, faster search.",
    )

    parser.add_argument(
        "-t", "--title", nargs="?", type=str, required=False, help="Title for app"
    )

    parser.add_argument("path", help="Path to the corpus")

    return vars(parser.parse_args())

class Site(object):
    def __init__(self, path, title=None, load=True):
        self.path = path
        self.title = title or f"Explore: {os.path.basename(path)}"
        self.corpus = Corpus(self.path).load()
        self.colors = {"background": "#ffffff", "text": "#7FDBFF"}
        ALL_DATA['corpus'] = self.corpus
        ALL_DATA['initial_table'] = self.corpus.table(show='x', subcorpora='f')
        app.layout = html.Div(
            style={"backgroundColor": self.colors["background"]},
            children=[
                html.H1(
                    children=self.title,
                    style={"textAlign": "center", "color": self.colors["text"]},
                )
            ],
        )
        self._build_layout()

    def add(self, kind="div", data=None, add=None, id=None, **kwargs):
        comp = _make_component(kind, data, add, id, **kwargs)
        app.layout.children.append(comp)

    def _build_search_space(self):
        self.add("markdown", "## Search space\n\nCreate a new search here")
        cols = ["file", "s", "i"] + list(self.corpus.columns)
        cols = [dict(label=LABELS.get(i, i.title()), value=i) for i in cols]
        cols += [dict(label="Dependencies", value="d"), dict(label="Trees", value="t")]
        dropdown = dcc.Dropdown(id="colselect", options=cols, value="w")
        df = ALL_DATA['corpus']
        df = df.drop("parse", axis=1, errors="ignore")
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict("rows")

        search_space = html.Div(
            [
                html.Div(dropdown),
                html.Div(dcc.Input(id="input-box", type="text")),
                html.Button("Submit", id="button"),
                daq.BooleanSwitch(id="skip-switch", on=False),
                html.Div(
                    id="output-container-button",
                    children="Enter a value and press submit",
                ),
                dash_table.DataTable(
                    id="conll-view",
                    columns=columns,
                    data=data,
                    editable=True,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    row_selectable="multi",
                    row_deletable=True,
                    selected_rows=[],
                    page_action="native",
                    page_current=0,
                    page_size=50,
                )
            ]
        )
        print('ADDING SEARCH SPACE TO SITE')
        app.layout.children.append(search_space)

    def _build_table_space(self, data):
        self.add("markdown", "## Table space")
        cols = ["file", "s", "i"] + list(self.corpus.columns)
        cols = [dict(label=LABELS.get(i, i.title()), value=i) for i in cols]
        show_check = dcc.Checklist(id="show-for-table", options=cols, value=[])
        subcorpora_drop = dcc.Dropdown(
            id="subcorpora-for-table", options=cols, value="file"
        )
        relative_drop = dcc.Dropdown(
            id="relative-for-table",
            options=[
                {"label": "Absolute frequency", "value": "ff"},
                {"label": "Relative of result", "value": "tf"},
                {"label": "Relative of corpus", "value": "nf"},
                {"label": "Keyness: log likelihood", "value": "fl"},
                {"label": "Keyness: percent difference", "value": "fp"},
            ],
            value="tf",
        )
        sort_drop = dcc.Dropdown(
            id="sort-for-table",
            options=[
                {"label": "Total", "value": "total"},
                {"label": "Infrequent", "value": "infreq"},
                {"label": "Alphabetical", "value": "name"},
                {"label": "Increasing", "value": "increase"},
                {"label": "Decreasing", "value": "decrease"},
                {"label": "Static", "value": "static"},
                {"label": "Turbulent", "value": "turbulent"},
            ],
            value="total",
        )
        table_space = html.Div(
            [
                html.Div(show_check),
                html.Div(subcorpora_drop),
                html.Div(sort_drop),
                html.Div(relative_drop),
                html.Button("Update", id="update-button"),
                html.Div(id="table-generate-outer", children="Generate a new table"),
            ]
        )
        print('ADDING TABLE')
        app.layout.children.append(table_space)
        self.add("datatable", data, id="freq-table")

    def _build_layout(self):
        self._build_search_space()
        nouns = self.corpus.just.x.NOUN
        tab = nouns.table(subcorpora="file", show="l", relative=True)
        self.add("bar", tab.square(20), id="main-chart")
        self.add("markdown", "## Concordancing")
        self.add("datatable", nouns.conc().head(100), id="conctable")
        self._build_table_space(tab.square(20))




@app.callback(
    [
        dash.dependencies.Output("conll-view", "columns"),
        dash.dependencies.Output("conll-view", "data")
        # todo: search from...
        # dash.dependencies.Output('search-from', 'children')
    ],
    [
        dash.dependencies.Input("colselect", "value"),
        dash.dependencies.Input("skip-switch", "on"),
    ],
    [dash.dependencies.State("input-box", "value")],
)
def new_search(col, skip, search_string):
    print("NEW SEARCH CALLBACK", col, skip, search_string)
    # seems to callback on load, don't know why
    # this is therefore what is shown initially
    if search_string is None:
        return _make_datatable(ALL_DATA['corpus'], "conll-view", update=True)
    method = "just" if not skip else "skip"
    df = getattr(getattr(ALL_DATA['corpus'], method), col)(search_string.strip())
    this_search = (col, skip, search_string, df.index)
    print('MADE IT HERE')
    return _make_datatable(df, "conll-view", update=True)

@app.callback(
    [
        dash.dependencies.Output("main-chart", "figure"),
        dash.dependencies.Output("freq-table", "columns"),
        dash.dependencies.Output("freq-table", "data")
    ],
    [
        dash.dependencies.Input("show-for-table", "value"),
        dash.dependencies.Input("subcorpora-for-table", "value"),
        dash.dependencies.Input("relative-for-table", "value"),
        dash.dependencies.Input("sort-for-table", "value"),
    ],
)
def new_table(show, subcorpora, relkey, sort):
    print("NEW TABLE CALLBACK", show, subcorpora, relkey, sort)
    if not show:
        table = ALL_DATA['initial_table']
        cols, data = _make_datatable(table, "freq-table", update=True)
        return (_df_to_figure(table), cols, data)
    relative, keyness = _translate_relative(relkey)
    if relative is None:
        relative = ALL_DATA['corpus']
    to_search = ALL_DATA['corpus']  # if not search_from else search_from...
    # todo: preload the simple ones
    table = to_search.table(
        show=show,
        subcorpora=subcorpora,
        relative=relative,
        keyness=keyness,
        sort=sort,
    )
    cols, data = _make_datatable(table, "freq-table", update=True)
    return (_df_to_figure(table), cols, data)


def _make_datatable(df, id, update=False):
    df = df.drop("parse", axis=1, errors="ignore")
    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict("rows")
    if update:
        return columns, data
    return dash_table.DataTable(
        id=id,
        columns=columns,
        data=data,
        editable=True,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        row_selectable="multi",
        row_deletable=True,
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=50,
    )

def _df_to_figure(df, kind="bar"):
    datapoints = list()
    for row_name, row in df.T.iterrows():
        datapoints.append(PLOTTERS[kind](row_name, row))
    layout = dict(
        # plot_bgcolor=self.colors["background"],
        # paper_bgcolor=self.colors["background"],
        # font=dict(color=self.colors["text"]),
    )
    return dict(data=datapoints, layout=layout)


def _translate_relative(inp):
    mapping = dict(t=True, f=False, n=ALL_DATA['corpus'], l="ll", p="pd")
    assert len(inp) == 2
    return mapping[inp[0]], mapping[inp[1]]



if __name__ == "__main__":
    site = Site(**_parse_cmdline_args())
    app.run_server(debug=True)
