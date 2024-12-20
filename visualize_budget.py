import pandas as pd
from dash import Dash, dcc, html
import plotly.graph_objects as go
import plotly.express as px
from threading import Timer
from main import kill_port, open_browser
from utils import (
    configure_pie_traces,
    parse_args,
    set_current_theme,
    DATA_FILE,
    DEFAULT_STYLE,
    DIVIDER_STYLE,
    H1_STYLE,
    H2_STYLE,
    PIE_SCHEME,
    PORT_BUDGET,
    SHOW_DOLLAR,
    TABLE_HEADER_STYLE,
    TABLE_ROW_STYLE,
    TABLE_SECTION_TITLE_STYLE,
    TABLE_STYLE
)

def visualize_budget(data_file):
    """
    Generate and display budget visualizations using Dash.

    Args:
        data_file (str): Path to the CSV file containing budget data.
    """
    # Free the port for the budget visualization
    kill_port(PORT_BUDGET)

    # Load budget data
    data = pd.read_csv(data_file)

    # Split data into income and expenses
    income_data = data[data["Category"].str.lower() == "income"].sort_values(by="Amount", ascending=False)
    expenses_data = data[data["Category"].str.lower() == "expenses"].sort_values(by="Amount", ascending=False)

    if income_data.empty or expenses_data.empty:
        raise ValueError("Both income and expenses data must be present.")

    # Calculate totals and savings
    total_income = income_data["Amount"].sum()
    total_expenses = expenses_data["Amount"].sum()
    savings = total_income - total_expenses

    # Prepare data for the Sankey diagram
    nodes = []
    links = {"source": [], "target": [], "value": [], "color": []}
    combined_colors = PIE_SCHEME * ((len(income_data) + len(expenses_data)) // len(PIE_SCHEME) + 1)

    def add_node(label):
        """Add a unique node to the Sankey diagram."""
        if label not in nodes:
            nodes.append(label)
        return nodes.index(label)

    # Add income nodes to the Sankey diagram
    for i, row in income_data.iterrows():
        source_idx = add_node(row["Source"])
        budget_idx = add_node("Budget")
        links["source"].append(source_idx)
        links["target"].append(budget_idx)
        links["value"].append(row["Amount"])
        links["color"].append(combined_colors[i])

    # Add expense nodes to the Sankey diagram
    for i, row in expenses_data.iterrows():
        budget_idx = add_node("Budget")
        expense_idx = add_node(row["Source"])
        links["source"].append(budget_idx)
        links["target"].append(expense_idx)
        links["value"].append(row["Amount"])
        links["color"].append(combined_colors[len(income_data) + i])

    # Add savings node if savings are positive
    if savings > 0:
        budget_idx = add_node("Budget")
        savings_idx = add_node("Savings")
        links["source"].append(budget_idx)
        links["target"].append(savings_idx)
        links["value"].append(savings)
        links["color"].append("#197")  # Custom savings color

    # Create Dash app
    app = Dash(__name__)

    # Layout for the Dash app
    app.layout = html.Div(style=DEFAULT_STYLE, children=[
        # Title Section
        html.H1("Budget Visualization", style=H1_STYLE),
        html.Hr(style=DIVIDER_STYLE),

        # Cash Flow Section (Sankey Diagram)
        html.Div(style={
            "backgroundColor": TABLE_STYLE["backgroundColor"],
            "padding": "30px",
            "borderRadius": "15px",
            "marginBottom": "30px",
            "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.25)"
        }, children=[
            html.H2("Cash Flow", style=H2_STYLE),
            dcc.Graph(
                figure=go.Figure(go.Sankey(
                    node=dict(
                        pad=25,
                        thickness=30,
                        line=dict(color=DEFAULT_STYLE["color"], width=0.5),
                        label=nodes,
                        color=DEFAULT_STYLE["color"]
                    ),
                    link=dict(
                        source=links["source"],
                        target=links["target"],
                        value=links["value"],
                        color=links["color"],
                        hovertemplate="<b>%{source.label} → %{target.label}</b><br>"
                                      f"{'Amount: $%{value:,.2f}' if SHOW_DOLLAR else 'Percentage: %{value:.1f}%'}<extra></extra>"
                    )
                )).update_layout(
                    margin=dict(l=50, r=50, t=50, b=50),
                    height=600,
                    paper_bgcolor=TABLE_STYLE["backgroundColor"],
                )
            )
        ]),
        html.Hr(style=DIVIDER_STYLE),

        # Expense Breakdown Section (Pie Chart)
        html.Div(style={
            "backgroundColor": TABLE_STYLE["backgroundColor"],
            "padding": "20px",
            "borderRadius": "10px",
            "marginBottom": "20px"
        }, children=[
            html.H2("Expense Breakdown", style=H2_STYLE),
            dcc.Graph(
                figure=configure_pie_traces(
                    px.pie(
                        expenses_data,
                        values="Amount",
                        names="Source",
                    ).update_layout(
                        paper_bgcolor=TABLE_STYLE["backgroundColor"],
                        font=dict(
                            family=DEFAULT_STYLE["fontFamily"],
                            color=DEFAULT_STYLE["color"]
                        )
                    ),
                    expenses_data["Amount"],
                    show_dollar=SHOW_DOLLAR
                )
            )
        ]),
        html.Hr(style=DIVIDER_STYLE),

        # Income and Expense Table Section
        html.Div(style={
            "backgroundColor": TABLE_STYLE["backgroundColor"],
            "padding": "20px",
            "borderRadius": "10px",
            "marginBottom": "20px"
        }, children=[
            html.H2("Details", style=H2_STYLE),

            # Income Table
            html.Table([
                # Income Section Header
                html.Tr([
                    html.Th("Income", colSpan=2, style=TABLE_SECTION_TITLE_STYLE)
                ]),
                # Income Table Header
                html.Tr([
                    html.Th("Source", style={**TABLE_HEADER_STYLE, "width": "50%"}),
                    html.Th("Amount", style={**TABLE_HEADER_STYLE, "width": "50%"})
                ]),
                # Income Table Rows
                *[
                    html.Tr([
                        html.Td(row["Source"], style={**TABLE_ROW_STYLE, "width": "50%"}),
                        html.Td(
                            f"${row['Amount']:,.2f}" if SHOW_DOLLAR else f"{(row['Amount'] / total_income) * 100:.1f}%",
                            style={**TABLE_ROW_STYLE, "width": "50%"}
                        )
                    ])
                    for _, row in income_data.iterrows()
                ]
            ], style=TABLE_STYLE),

            html.Hr(style=DIVIDER_STYLE),

            # Expenses Table
            html.Table([
                # Expenses Section Header
                html.Tr([
                    html.Th("Expenses", colSpan=2, style=TABLE_SECTION_TITLE_STYLE)
                ]),
                # Expenses Table Header
                html.Tr([
                    html.Th("Source", style={**TABLE_HEADER_STYLE, "width": "50%"}),
                    html.Th("Amount", style={**TABLE_HEADER_STYLE, "width": "50%"})
                ]),
                # Expenses Table Rows
                *[
                    html.Tr([
                        html.Td(row["Source"], style={**TABLE_ROW_STYLE, "width": "50%"}),
                        html.Td(
                            f"${row['Amount']:,.2f}" if SHOW_DOLLAR else f"{(row['Amount'] / total_expenses) * 100:.1f}%",
                            style={**TABLE_ROW_STYLE, "width": "50%"}
                        )
                    ])
                    for _, row in expenses_data.iterrows()
                ]
            ], style=TABLE_STYLE)
        ])
    ])

    # Automatically open the app in the browser
    Timer(1, open_browser, args=[PORT_BUDGET]).start()

    # Run the Dash server
    app.run_server(debug=True, use_reloader=False, port=PORT_BUDGET)


if __name__ == "__main__":
    args = parse_args()
    SHOW_DOLLAR = args.show_dollar
    set_current_theme(args.theme)
    visualize_budget(DATA_FILE)