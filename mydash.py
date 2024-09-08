from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import ssl
import sqlite3

ssl._create_default_https_context = ssl._create_unverified_context

# df = pd.read_csv(
#     "http://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv"
# )

# Read all the customer records from the sqlite table customers
con = sqlite3.connect("data/chinook.db")
df = pd.read_sql_query("SELECT * from customers", con)

# Verify that result of SQL query is stored in the dataframe
print(df.head())

con.close()

app = Dash()

app.layout = [
    html.H1(children="Title of Dash App", style={"textAlign": "center"}),
    dcc.Input(id="input-box", type="text", value="What are you lookin for?", style={"width": "100%"}),
    # Search button
    html.Button("Search", id="search-button", style={"width": "100%"}),
    # dcc.Dropdown(df.country.unique(), "Canada", id="dropdown-selection"),
    dcc.Graph(id="graph-content"),
]

@callback(Output("graph-content", "figure"), Input("dropdown-selection", "value"))
def update_graph(value):
    dff = df
    return px.line(dff, x="year", y="pop")


if __name__ == "__main__":
    app.run(debug=True)
