import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import sqlite3
import ssl
from sqlalchemy import create_engine
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_openai import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain.prompts import ChatPromptTemplate

# Set your OpenAI API key (DO NOT CHANGE THIS)
OPENAI_API_KEY = "<YOUR_OPENAI_API_KEY>"

# Initialize the OpenAI LLM with the API key
llm = OpenAI(openai_api_key=OPENAI_API_KEY)

# Database connection and SQL agent setup
engine = create_engine("sqlite:///ABS_2021_Census.db")
ssl._create_default_https_context = ssl._create_unverified_context

# Create a connection to your SQLite database
db = SQLDatabase.from_uri("sqlite:///ABS_2021_Census.db")

# Initialize the toolkit for SQL interaction
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Fetch database schema (optional but can help LLM understand the structure)
database_schema = db.get_table_info()


# Custom function to generate SQL query without executing it
def generate_sql_query(input_text):
    # Use the ChatPromptTemplate to create a prompt for generating SQL queries
    query_prompt_template = ChatPromptTemplate.from_template(
        "Given the following database schema:\n{database_schema}\nGenerate a SQL query for the following task: {input_text}, but do not execute it."
    )
    # Combine the toolkit and LLM to create the final prompt and execute it to get the query
    prompt = query_prompt_template.format(
        database_schema=database_schema, input_text=input_text
    )
    # Use the toolkit LLM to get the SQL query
    sql_query = toolkit.llm(prompt)
    return sql_query


# Dash App Setup
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        # Title
        dbc.Row(dbc.Col(html.H1("Atlas", className="text-center mb-4"))),
        # Search Box
        dbc.Row(
            dbc.Col(
                dcc.Input(
                    id="input-box",
                    type="text",
                    placeholder="What are you looking for?",
                    className="form-control",
                )
            )
        ),
        # Search Button
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    "Search",
                    id="search-button",
                    className="btn btn-primary mt-2 w-100",
                    n_clicks=0,
                )
            )
        ),
        # SQL Query Display
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H5("SQL Query:"),
                        html.Pre(
                            id="sql-query",
                            style={
                                "backgroundColor": "#f8f9fa",
                                "padding": "10px",
                                "border": "1px solid #dee2e6",
                            },
                        ),
                    ],
                    className="mt-3",
                )
            )
        ),
        # Scrollable Table Display
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.H5("SQL Data Table:"),
                        dash_table.DataTable(
                            id="data-table",
                            columns=[],  # Empty initially, will be populated after search
                            data=[],
                            style_table={
                                "overflowY": "auto",
                                "height": "300px",
                            },  # Enable vertical scroll and limit height
                            style_cell={"textAlign": "left"},
                            style_header={
                                "backgroundColor": "rgb(230, 230, 230)",
                                "fontWeight": "bold",
                            },
                        ),
                    ],
                    className="mt-3",
                )
            )
        ),
        # Graph Display
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id="graph-content", style={"display": "none"}
                )  # Initially hide the graph
            )
        ),
        # Error Message
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="error-message", style={"color": "red", "display": "none"}
                )  # Error message for empty input
            )
        ),
    ]
)


# Update the graph selection function to reflect the correct columns in your data
def select_best_graph(data):
    # Replace with your actual columns ("SA2_Name", "Household_Income:_$2000-$2499:_Total")
    return px.bar(
        data,
        x="SA2_Name",
        y="Household_Income:_$2000-$2499:_Total",
        title="Bar Chart: SA2 Name vs Household Income",
    )


@app.callback(
    [
        Output("graph-content", "figure"),
        Output("graph-content", "style"),
        Output("error-message", "children"),
        Output("error-message", "style"),
        Output("data-table", "columns"),
        Output("data-table", "data"),
        Output("sql-query", "children"),
    ],
    [Input("search-button", "n_clicks")],
    [State("input-box", "value")],
)
def update_graph(n_clicks, search_value):
    if n_clicks is None or not search_value:
        return (
            {},
            {"display": "none"},
            "Please enter a search term.",
            {"display": "block"},
            [],
            [],
            "",
        )

    # Store the input value in a variable
    stored_input_value = search_value
    print(f"Stored Input Value: {stored_input_value}")

    try:
        # Generate the SQL query based on input
        sql_query = f"""SELECT "SA2_Name", "Household_Income:_$2000-$2499:_Total"
FROM ABS_2021_Census
WHERE "Household_Income:_$2000-$2499:_Total" > 700"""

        # Read the query results from the SQLite database
        con = sqlite3.connect("Data/ABS_2021_Census.db")
        df = pd.read_sql_query(sql_query, con)
        con.close()

        # Prepare the table data for Dash DataTable
        columns = [{"name": i, "id": i} for i in df.columns]
        data = df.to_dict("records")

        # Select the most relevant graph based on data characteristics
        fig = select_best_graph(df)

        # Improve graph aesthetics
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
            title=dict(text="Graph Display", font=dict(size=20), x=0.5),
            xaxis=dict(title="SA2 Name", titlefont=dict(size=15)),
            yaxis=dict(title="Household Income", titlefont=dict(size=15)),
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Rockwell"),
        )

        return (
            fig,
            {"display": "block"},
            "",
            {"display": "none"},
            columns,
            data,
            sql_query,
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        return (
            {},
            {"display": "none"},
            f"Error: {str(e)}",
            {"display": "block"},
            [],
            [],
            "",
        )


if __name__ == "__main__":
    app.run_server(debug=True)
