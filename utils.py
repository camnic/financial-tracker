import argparse
import os
from dotenv import dotenv_values
from dash import html, dcc

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
    Parse command-line arguments for visualization options.
    
    Returns:
        argparse.Namespace: Parsed arguments with `show_dollar` and `theme`.
    """
    parser = argparse.ArgumentParser(description="Visualize Portfolio")
    parser.add_argument("--show-dollar", type=lambda x: x.lower() in ["true", "1", "yes"], default=True, help="Show dollar values")
    parser.add_argument("--theme", type=str, default="blue", help="Theme to use")
    return parser.parse_args()

def get_colors(theme_name):
    """
    Returns the selected theme's color palette.

    Args:
        theme_name (str): The name of the theme to retrieve. 
                          Must be a key in the THEMES dictionary.

    Returns:
        dict: A dictionary containing the color palette for the specified theme.
              Keys typically include 'light', 'medium', 'dark', 'bold', and 'white'.

    Raises:
        ValueError: If the provided theme_name does not exist in the THEMES dictionary.
    """
    if theme_name in THEMES:
        return THEMES[theme_name]
    raise ValueError(f"Theme '{theme_name}' does not exist. Available themes are: {', '.join(THEMES.keys())}.")

def set_current_theme(theme_name):
    """
    Updates the current theme and refreshes all style configurations dynamically.

    Args:
        theme_name (str): The name of the theme to set as the current theme. 
                          Must be a key in the THEMES dictionary.

    Raises:
        ValueError: If the provided theme_name does not exist in the THEMES dictionary.
    """
    global current_theme, DEFAULT_COLORS, DEFAULT_STYLE, H1_STYLE, H2_STYLE, DIVIDER_STYLE, TABLE_STYLE, TABLE_HEADER_STYLE, TABLE_ROW_STYLE, TABLE_SECTION_TITLE_STYLE

    if theme_name not in THEMES:
        raise ValueError(f"Invalid theme: {theme_name}")
    
    current_theme = theme_name
    DEFAULT_COLORS = get_colors(current_theme)

    DEFAULT_STYLE.update({
        "fontFamily": FONT_FAMILY,
        "fontSize": "18px",
        "backgroundColor": DEFAULT_COLORS["dark"],
        "color": DEFAULT_COLORS["white"],
        "margin": 0,
        "padding": "12px",
        "lineHeight": "1.6",
    })

    H1_STYLE.update({
        "color": DEFAULT_COLORS["white"],
    })
    H2_STYLE.update({
        "color": DEFAULT_COLORS["light"],
    })
    DIVIDER_STYLE.update({
        "border": f"1px solid {DEFAULT_COLORS['white']}",
        "color": DEFAULT_COLORS["bold"],
    })
    TABLE_STYLE.update({
        "backgroundColor": DEFAULT_COLORS["bold"],
        "color": DEFAULT_COLORS["white"],
    })
    TABLE_HEADER_STYLE.update({
        "backgroundColor": DEFAULT_COLORS["medium"],
        "color": DEFAULT_COLORS["white"],
        "border": f"1px solid {DEFAULT_COLORS['light']}",
    })
    TABLE_ROW_STYLE.update({
        "border": f"1px solid {DEFAULT_COLORS['light']}",
    })
    TABLE_SECTION_TITLE_STYLE.update({
        "backgroundColor": DEFAULT_COLORS["light"],
        "color": DEFAULT_COLORS["white"],
    })

def get_layout():
    """
    Constructs the layout for the Dash application.

    Returns:
        dash.html.Div: A Dash HTML Div element representing the main page layout.
    """
    theme_colors = get_colors(current_theme)
    style = {
        **DEFAULT_STYLE,
        "backgroundColor": theme_colors["dark"],
        "color": theme_colors["white"]
    }
    return html.Div(
        style=style,
        children=[
            html.H1("Main Menu", style={"textAlign": "center", "fontSize": "24px"}),
            html.Hr(),
            # Theme Dropdown
            html.Div(
                [
                    html.Label("Select Theme:", style={"fontSize": "16px", "fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="theme_dropdown",
                        options=[{"label": theme.title(), "value": theme} for theme in THEMES],
                        value=current_theme,
                        style={"width": "50%", "margin": "0 auto", "color": DEFAULT_COLORS["bold"]},
                    ),
                ],
                style={"textAlign": "center", "marginBottom": "20px"},
            ),
            # Placeholder for dynamically updated content
            html.Div(id="main_content", children=generate_main_content(current_theme)),
        ]
    )

def generate_main_content(theme):
    theme_colors = get_colors(theme)
    style = {
        **DEFAULT_STYLE,
        "backgroundColor": theme_colors["dark"],
        "color": theme_colors["white"]
    }
    return html.Div(
        style=style,
        children=[
            html.H1("Main Menu", style={"textAlign": "center", "fontSize": "24px"}),
            html.Hr(),
            # Feature Flag Section
            html.Div(
                [
                    html.Label(id="feature_flag_label", style={"fontSize": "16px", "fontWeight": "bold"}),
                    html.Button(
                        id="feature_flag_button",
                        n_clicks=0,
                        children="Show",
                        style={"margin": "10px"},
                    ),
                ],
                style={"textAlign": "center", "marginBottom": "20px"},
            ),
            # Script Buttons
            html.Div(
                [
                    html.Button("Calculate Portfolio", id="calculate_portfolio", n_clicks=0, style={"margin": "10px"}),
                    html.Button("Visualize Portfolio", id="visualize_portfolio", n_clicks=0, style={"margin": "10px"}),
                    html.Button("Visualize Budget", id="visualize_budget", n_clicks=0, style={"margin": "10px"}),
                ],
                style={"textAlign": "center"},
            ),
            # Output Section
            html.Div(id="output", style={"textAlign": "center", "marginTop": "20px", "fontSize": "16px"}),
        ],
    )

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
    "current_value": "#dda15e"
}

PIE_SCHEME = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf"
]

# Theme Options
THEMES = {
    "blue": {
        "light": "#00a6fb",
        "medium": "#0582ca",
        "dark": "#006494",
        "bold": "#003554",
        "white": "#eef4ed"
    },
    "purple": {
        "light": "#be95c4",
        "medium": "#9f86c0",
        "dark": "#5e548e",
        "bold": "#231942",
        "white": "#eef4ed"
    },
    "green": {
        "light": "#90a955",
        "medium": "#4f772d",
        "dark": "#31572c",
        "bold": "#132a13",
        "white": "#eef4ed"
    },
    "red": {
        "light": "#c9cba3",
        "medium": "#e26d5c",
        "dark": "#723d46",
        "bold": "#472d30",
        "white": "#eef4ed"
    },
    "orange": {
        "light": "#ffdd00",
        "medium": "#ffc300",
        "dark": "#ffa200",
        "bold": "#ff7b00",
        "white": "#eef4ed"
    }
}

# Theme Selection
main_background = "#4F4F4F"
current_theme = "blue"
DEFAULT_COLORS = get_colors(current_theme)

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