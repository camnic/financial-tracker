import os
import psutil
from dash import Dash, html, dcc, Input, Output, State, callback_context
import webbrowser
from threading import Timer
from utils import (
    DEFAULT_COLORS,
    DEFAULT_STYLE,
    PORT_API,
    PORT_BUDGET,
    PORT_MAIN,
    PORT_PORTFOLIO,
    SHOW_DOLLAR,
    THEMES,
    current_theme,
    main_background,
    parse_args,
    get_colors,
    set_current_theme,
    generate_main_content
)

FUNCTIONS = {
    "calculate_portfolio": ("calculate_portfolio.py", PORT_API),
    "visualize_portfolio": ("visualize_portfolio.py", PORT_PORTFOLIO),
    "visualize_budget": ("visualize_budget.py", PORT_BUDGET)
}

def kill_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    proc.kill()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

def open_browser(port):
    webbrowser.open_new(f"http://127.0.0.1:{port}")

def run_function(script_name, port, show_dollar, theme):
    kill_port(port)
    os.system(f"python3 {script_name} --show-dollar {str(show_dollar).lower()} --theme {theme} &")

def main():
    global current_theme, SHOW_DOLLAR

    kill_port(PORT_MAIN)

    app = Dash(__name__, suppress_callback_exceptions=True)

    def get_layout():
        theme_colors = get_colors(current_theme)
        style = {
            **DEFAULT_STYLE,
            "backgroundColor": main_background
        }
        return html.Div(
            style=style,
            children=[
                # Theme Dropdown Section
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
                # Main Content Section (Dynamic Content)
                html.Div(
                    id="main_content",
                    style={"padding": "20px"},
                    children=generate_main_content(current_theme),
                ),
            ],
        )

    @app.callback(
        [Output("feature_flag_label", "children"), Output("feature_flag_button", "children")],
        Input("feature_flag_button", "n_clicks"),
    )
    def toggle_feature_flag(n_clicks):
        global SHOW_DOLLAR
        SHOW_DOLLAR = n_clicks % 2 == 0
        return ("Balance Visible" if SHOW_DOLLAR else "Balance Hidden",
                "Hide" if SHOW_DOLLAR else "Show")

    @app.callback(
        Output("output", "children"),
        [Input("calculate_portfolio", "n_clicks"),
         Input("visualize_portfolio", "n_clicks"),
         Input("visualize_budget", "n_clicks")],
        State("theme_dropdown", "value"),
    )
    def handle_button_click(calc_clicks, vis_port_clicks, vis_budget_clicks, selected_theme):
        triggered = callback_context.triggered
        if not triggered:
            return "No action taken yet."

        button_id = triggered[0]["prop_id"].split(".")[0]
        if button_id in FUNCTIONS:
            current_theme = selected_theme
            balance_visibility = "visible" if SHOW_DOLLAR else "hidden"
            script_name, port = FUNCTIONS[button_id]
            run_function(script_name, port, SHOW_DOLLAR, current_theme)
            return html.Div([
                html.Div(f"Running: {button_id.replace('_', ' ').title()}", style={"fontWeight": "bold"}),
                html.Div(f"Theme: {current_theme.title()}"),
                html.Div(f"Balance: {balance_visibility.title()}")
            ])

        return "Invalid action."
    
    app.layout = get_layout()
    @app.callback(
        Output("theme_dropdown", "value"),
        Input("theme_dropdown", "value"),
    )
    def update_theme(selected_theme):
        global current_theme
        if callback_context.triggered and "theme_dropdown" in callback_context.triggered[0]["prop_id"]:
            current_theme = selected_theme
            set_current_theme(selected_theme)
        return selected_theme
    
    @app.callback(
        Output("main_content", "children"),
        Input("theme_dropdown", "value"),
    )
    def update_main_content(selected_theme):
        global current_theme
        if callback_context.triggered and "theme_dropdown" in callback_context.triggered[0]["prop_id"]:
            current_theme = selected_theme
            set_current_theme(selected_theme)
        return generate_main_content(selected_theme)

    Timer(1, open_browser, args=[PORT_MAIN]).start()
    app.run_server(debug=True, use_reloader=False, port=PORT_MAIN)


if __name__ == "__main__":
    args = parse_args()
    SHOW_DOLLAR = args.show_dollar
    set_current_theme(args.theme)
    main()