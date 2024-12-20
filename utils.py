import argparse
import os
from dotenv import dotenv_values

# Load API keys from environment file
API_KEYS = dotenv_values("input/api_key.md")
ALPHA_VANTAGE_API_KEY = API_KEYS.get("ALPHA_VANTAGE_API_KEY")

# Constants
LONG_TERM_HOLD_YEARS = 2

# Feature Flags
SHOW_DOLLAR = True

# File Paths
INPUT_FILE = "input/portfolio.csv"
TEMP_FILE = "input/temp_portfolio.csv"
DATA_FILE = "input/income_expenses.csv"

# Ports
PORT_MAIN = 8050
PORT_PORTFOLIO = 8051
PORT_BUDGET = 8052
PORT_API = 8053

# Colors
GAIN_COLOR_SCHEME = {
    "positive_long": "#a7c957",
    "positive_short": "#386641",
    "negative_short": "#bc4749",
    "negative_long": "#9b2226",
    "no_date": "#219ebc",
}
CONTRIBUTION_COLORS = {
    "investment": "#606c38",
    "current_value": "#dda15e"}

COLOR_SCHEME = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf"
]

DEFAULT_COLORS = {
    "light": "#8da9c4",
    "medium": "#134074",
    "dark": "#13315c",
    "bold": "#0b2545",
    "white": "#eef4ed"
}

# Font Configuration
FONT_FAMILY = "Arial, sans-serif"

# Default Styles
DEFAULT_STYLE = {
    "fontFamily": FONT_FAMILY,
    "fontSize": "18px",
    "backgroundColor": DEFAULT_COLORS["dark"],
    "color": DEFAULT_COLORS["white"],
    "margin": 0,
    "padding": "12px",
    "lineHeight": "1.6",
}

# Header Styles
H1_STYLE = {
    "textAlign": "center",
    "fontFamily": FONT_FAMILY,
    "fontSize": "26px",
    "marginBottom": "20px",
    "marginTop": "10px",
    "color": DEFAULT_COLORS["white"],
    "lineHeight": "1.5"
}

H2_STYLE = {
    "textAlign": "center",
    "fontFamily": FONT_FAMILY,
    "fontWeight": "bold",
    "fontSize": "22px",
    "marginBottom": "10px",
    "marginTop": "10px",
    "color": DEFAULT_COLORS["light"],
    "lineHeight": "1.4"
}

# Divider Style
DIVIDER_STYLE = {
    "border": f"1px solid {DEFAULT_COLORS['white']}",
    "marginTop": "20px",
    "marginBottom": "20px",
    "color": DEFAULT_COLORS["bold"]
}

# Table Styles
TABLE_STYLE = {
    "width": "100%",
    "margin": "auto",
    "borderCollapse": "collapse",
    "backgroundColor": DEFAULT_COLORS["bold"],
    "color": DEFAULT_COLORS["white"],
    "fontFamily": FONT_FAMILY,
    "fontSize": "14px",
    "lineHeight": "1.6"
}

TABLE_HEADER_STYLE = {
    "fontWeight": "bold",
    "backgroundColor": DEFAULT_COLORS["medium"],
    "color": DEFAULT_COLORS["white"],
    "textAlign": "center",
    "padding": "10px",
    "border": f"1px solid {DEFAULT_COLORS['light']}"
}

TABLE_ROW_STYLE = {
    "textAlign": "center",
    "padding": "8px",
    "border": f"1px solid {DEFAULT_COLORS['light']}"
}

TABLE_SECTION_TITLE_STYLE = {
    "textAlign": "center",
    "fontWeight": "bold",
    "fontSize": "18px",
    "marginBottom": "10px",
    "marginTop": "10px",
    "backgroundColor": DEFAULT_COLORS["light"],
    "color": DEFAULT_COLORS["white"],
    "padding": "10px"
}

# Function Definitions
def configure_pie_traces(figure, values, show_dollar=True):
    """
    Configure the traces for a pie chart.
    
    Args:
        figure: The plotly pie chart figure to configure.
        values (pd.Series): The values to display in the chart.
        show_dollar (bool): Whether to show dollar amounts or percentages.
        
    Returns:
        The updated figure with configured traces.
    """
    return figure.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>%{percent:.1%}"
            if not show_dollar else
            "<b>%{label}</b><br>%{value:$,.2f}<br>%{percent:.1%}"
        ),
        text=values.apply(lambda x: f"${x:,.0f}" if show_dollar else ""),
        textinfo="text+percent" if show_dollar else "percent"
    )

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments as a namespace.
    """
    parser = argparse.ArgumentParser(description="Visualization Script")
    parser.add_argument(
        "--show-dollar",
        type=lambda x: x.lower() in ["true", "1", "yes"],
        default=SHOW_DOLLAR,
        help="Feature flag for showing dollar values"
    )
    return parser.parse_args()