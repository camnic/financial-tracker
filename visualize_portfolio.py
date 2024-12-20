import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
from threading import Timer
from main import kill_port, open_browser
from utils import (
    SHOW_DOLLAR,
    TEMP_FILE,
    PORT_PORTFOLIO,
    DEFAULT_STYLE,
    H1_STYLE,
    H2_STYLE,
    DIVIDER_STYLE,
    GAIN_COLOR_SCHEME,
    CONTRIBUTION_COLORS,
    TABLE_STYLE,
    TABLE_HEADER_STYLE,
    TABLE_SECTION_TITLE_STYLE,
    TABLE_ROW_STYLE,
    configure_pie_traces,
    parse_args
)

def visualize_portfolio(portfolio_file):
    """
    Generate and display portfolio visualizations using Dash.

    Args:
        portfolio_file (str): Path to the portfolio CSV file.
    """
    # Free up the specified port before running the app
    kill_port(PORT_PORTFOLIO)

    # Load and validate the portfolio data
    portfolio = pd.read_csv(portfolio_file)
    valid_portfolio = portfolio[portfolio["Value"] > 0]

    if valid_portfolio.empty:
        raise ValueError("No valid data to visualize.")

    # Preprocess portfolio data
    valid_portfolio["Ticker"] = valid_portfolio["Ticker"].str.upper()
    valid_portfolio["Type"] = valid_portfolio["Type"].str.upper()
    valid_portfolio["Label"] = valid_portfolio.apply(
        lambda row: row["Ticker"] if row["Type"] not in ["CASH", "401K", "HSA"] else row["Type"],
        axis=1
    )

    # Summarize data for visualizations
    # 1. Distribution by Type for the pie chart
    type_summary = valid_portfolio.groupby("Type").agg({"Value": "sum"}).reset_index()
    type_summary["Percentage"] = (type_summary["Value"] / type_summary["Value"].sum()) * 100

    # 2. Gain/Loss data for the bar chart
    gain_loss_summary = valid_portfolio.sort_values(by="% Gain/Loss", ascending=False)

    # 3. Contribution details for historical performance
    contribution_summary = valid_portfolio[["Label", "Cost Basis", "Value", "Quantity", "Type"]].copy()
    contribution_summary["Investment"] = contribution_summary.apply(
        lambda row: row["Cost Basis"] if row["Type"] in ["CASH", "401K", "HSA"] else row["Cost Basis"] * row["Quantity"],
        axis=1
    )
    contribution_summary = contribution_summary[["Label", "Investment", "Value"]]

    # Set up Dash app
    app = Dash(__name__)

    app.layout = html.Div(
        style=DEFAULT_STYLE,
        children=[
            # Title
            html.H1("Portfolio Visualization", style=H1_STYLE),
            html.Hr(style=DIVIDER_STYLE),

            # Portfolio Distribution Section
            html.Div(
                style={
                    "backgroundColor": TABLE_STYLE["backgroundColor"],
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginBottom": "20px"
                },
                children=[
                    html.H2("Distribution", style=H2_STYLE),
                    dcc.Graph(
                        figure=configure_pie_traces(
                            px.pie(
                                type_summary,
                                values="Value",
                                names="Type"
                            ).update_layout(
                                paper_bgcolor=TABLE_STYLE["backgroundColor"],
                                font=dict(
                                    family=DEFAULT_STYLE["fontFamily"],
                                    color=DEFAULT_STYLE["color"]
                                )
                            ),
                            type_summary["Value"],
                            show_dollar=SHOW_DOLLAR
                        )
                    )
                ]
            ),
            html.Hr(style=DIVIDER_STYLE),

            # Gain/Loss Section
            html.Div(
                style={
                    "backgroundColor": TABLE_STYLE["backgroundColor"],
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginBottom": "20px"
                },
                children=[
                    html.H2("Gain/Loss", style=H2_STYLE),
                    dcc.Graph(
                        figure=go.Figure(
                            data=[
                                go.Bar(
                                    x=gain_loss_summary["Label"],
                                    y=gain_loss_summary["% Gain/Loss"],
                                    marker_color=gain_loss_summary.apply(
                                        lambda row: (
                                            GAIN_COLOR_SCHEME["positive_long"] if row["Long-Term Hold"] == "Green" and row["% Gain/Loss"] > 0 else
                                            GAIN_COLOR_SCHEME["positive_short"] if row["Long-Term Hold"] == "Red" and row["% Gain/Loss"] > 0 else
                                            GAIN_COLOR_SCHEME["negative_short"] if row["Long-Term Hold"] == "Red" and row["% Gain/Loss"] <= 0 else
                                            GAIN_COLOR_SCHEME["negative_long"] if row["Long-Term Hold"] == "Green" and row["% Gain/Loss"] <= 0 else
                                            GAIN_COLOR_SCHEME["no_date"]
                                        ),
                                        axis=1
                                    ),
                                    text=gain_loss_summary.apply(
                                        lambda row: f"${row['Gain/Loss']:,.2f} ({row['% Gain/Loss']:.1f}%)" if SHOW_DOLLAR else f"{row['% Gain/Loss']:.1f}%",
                                        axis=1
                                    ),
                                    textposition="outside",
                                    hovertemplate="<b>%{x}</b><br>Gain/Loss: %{text}<extra></extra>",
                                )
                            ]
                        ).update_layout(
                            xaxis=dict(
                                title=dict(
                                    text="Ticker/Type",
                                    font=dict(
                                        size=int(DEFAULT_STYLE["fontSize"].replace("px", "")),
                                        family=DEFAULT_STYLE["fontFamily"],
                                        color=DEFAULT_STYLE["color"]
                                    )
                                ),
                                tickfont=dict(color=DEFAULT_STYLE["color"]),
                                tickangle=45
                            ),
                            yaxis=dict(
                                title=dict(
                                    text="Gain/Loss (%)" if not SHOW_DOLLAR else "Gain/Loss ($)",
                                    font=dict(
                                        size=int(DEFAULT_STYLE["fontSize"].replace("px", "")),
                                        family=DEFAULT_STYLE["fontFamily"],
                                        color=DEFAULT_STYLE["color"]
                                    )
                                ),
                                tickfont=dict(color=DEFAULT_STYLE["color"])
                            ),
                            paper_bgcolor=TABLE_STYLE["backgroundColor"],
                            legend=dict(
                                itemsizing="constant",
                                traceorder="normal",
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                                font=dict(
                                    family=H2_STYLE["fontFamily"],
                                    color=H2_STYLE["color"]
                                )
                            )
                        )
                    )
                ]
            ),
            html.Hr(style=DIVIDER_STYLE),

            # Performance Section
            html.Div(
                style={
                    "backgroundColor": TABLE_STYLE["backgroundColor"],
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginBottom": "20px"
                },
                children=[
                    html.H2("Performance", style=H2_STYLE),
                    dcc.Graph(
                        figure=go.Figure(data=[
                            go.Bar(
                                name="Investment",
                                x=contribution_summary["Label"],
                                y=contribution_summary["Investment"],
                                marker_color=CONTRIBUTION_COLORS["investment"],
                                text=contribution_summary["Investment"].apply(
                                    lambda x: f"${x:,.2f}" if SHOW_DOLLAR else ""),
                                textposition="outside"
                            ),
                            go.Bar(
                                name="Current Value",
                                x=contribution_summary["Label"],
                                y=contribution_summary["Value"],
                                marker_color=CONTRIBUTION_COLORS["current_value"],
                                text=contribution_summary["Value"].apply(
                                    lambda x: f"${x:,.2f}" if SHOW_DOLLAR else ""),
                                textposition="outside"
                            )
                        ]).update_layout(
                            xaxis=dict(
                                title=dict(
                                    text="Ticker/Type",
                                    font=dict(
                                        size=int(DEFAULT_STYLE["fontSize"].replace("px", "")),
                                        family=DEFAULT_STYLE["fontFamily"],
                                        color=DEFAULT_STYLE["color"]
                                    )
                                ),
                                tickfont=dict(color=DEFAULT_STYLE["color"]),
                                tickangle=45
                            ),
                            yaxis=dict(
                                title=dict(
                                    text="Value ($)",
                                    font=dict(
                                        size=int(DEFAULT_STYLE["fontSize"].replace("px", "")),
                                        family=DEFAULT_STYLE["fontFamily"],
                                        color=DEFAULT_STYLE["color"]
                                    )
                                ),
                                tickfont=dict(color=DEFAULT_STYLE["color"])
                            ),
                            barmode="group",
                            paper_bgcolor=TABLE_STYLE["backgroundColor"],
                            legend=dict(
                                itemsizing="constant",
                                traceorder="normal",
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1,
                                font=dict(
                                    family=H2_STYLE["fontFamily"],
                                    color=H2_STYLE["color"]
                                )
                            ),
                            showlegend=True
                        )
                    )
                ]
            ),
            html.Hr(style=DIVIDER_STYLE),

            # Portfolio Summary Section
            html.Div(
                style={
                    "backgroundColor": TABLE_STYLE["backgroundColor"],
                    "padding": "20px",
                    "borderRadius": "10px",
                    "marginBottom": "20px"
                },
                children=(
                    [
                        html.H2("Portfolio Summary", style=H2_STYLE),
                        *[
                            html.Div(
                                children=[
                                    html.H3(f"{type_group}", style=TABLE_SECTION_TITLE_STYLE),
                                    html.Table(
                                        children=[
                                            html.Tr([
                                                html.Th("Ticker", style={**TABLE_HEADER_STYLE, "width": "16%"}),
                                                html.Th("Value", style={**TABLE_HEADER_STYLE, "width": "16%"}),
                                                html.Th("Quantity", style={**TABLE_HEADER_STYLE, "width": "16%"}),
                                                html.Th("Cost", style={**TABLE_HEADER_STYLE, "width": "16%"}),
                                                html.Th("Dollar Total Gain", style={**TABLE_HEADER_STYLE, "width": "16%"}),
                                                html.Th("Percentage Total Gain", style={**TABLE_HEADER_STYLE, "width": "16%"})
                                            ]),
                                            *[
                                                html.Tr([
                                                    html.Td(row["Ticker"], style={**TABLE_ROW_STYLE, "width": "16%"}),
                                                    html.Td(f"${row['Value']:,.2f}", style={**TABLE_ROW_STYLE, "width": "16%"}),
                                                    html.Td(f"{row['Quantity']:,}", style={**TABLE_ROW_STYLE, "width": "16%"}),
                                                    html.Td(
                                                        f"${row['Cost Basis'] * row['Quantity'] if row['Type'].upper() not in ['CASH', '401K', 'HSA'] else row['Cost Basis']:,.2f}",
                                                        style={**TABLE_ROW_STYLE, "width": "16%"}
                                                    ),
                                                    html.Td(f"${row['Gain/Loss']:,.2f}", style={**TABLE_ROW_STYLE, "width": "16%"}),
                                                    html.Td(f"{row['% Gain/Loss']:.2f}%", style={**TABLE_ROW_STYLE, "width": "16%"})
                                                ])
                                                for _, row in group.iterrows()
                                            ],
                                            html.Tr([
                                                html.Td(
                                                    "Total Value",
                                                    style={
                                                        **TABLE_ROW_STYLE,
                                                        "fontWeight": "bold",
                                                        "textAlign": "center",
                                                        "colSpan": 3
                                                    }
                                                ),
                                                html.Td(
                                                    f"${group['Value'].sum():,.2f}",
                                                    style={
                                                        **TABLE_ROW_STYLE,
                                                        "fontWeight": "bold",
                                                        "textAlign": "center",
                                                        "colSpan": 3
                                                    }
                                                )
                                            ])
                                        ],
                                        style=TABLE_STYLE
                                    )
                                ]
                            )
                            for type_group, group in sorted(
                                valid_portfolio.groupby("Type"),
                                key=lambda g: g[1]["Value"].sum(),
                                reverse=True
                            )
                        ],
                        html.Div(
                            style={
                                "marginTop": "20px",
                                "paddingTop": "10px",
                                "borderTop": f"1px solid {TABLE_STYLE['backgroundColor']}"
                            },
                            children=[
                                html.H3(
                                    f"Total Portfolio Value: ${valid_portfolio['Value'].sum():,.2f}",
                                    style={**TABLE_SECTION_TITLE_STYLE, "textAlign": "center"}
                                )
                            ]
                        )
                    ]
                ) if SHOW_DOLLAR else []
            )
        ]
    )

    # Open the app in the browser
    Timer(1, open_browser, args=[PORT_PORTFOLIO]).start()

    # Run the app server
    app.run_server(debug=True, use_reloader=False, port=PORT_PORTFOLIO)


if __name__ == "__main__":
    args = parse_args()
    SHOW_DOLLAR = args.show_dollar
    visualize_portfolio(TEMP_FILE)