import os
import psutil
from dash import Dash, html, Input, Output, callback_context
import webbrowser
from threading import Timer
from utils import PORT_MAIN, PORT_PORTFOLIO, PORT_BUDGET, PORT_API, DEFAULT_STYLE

# Global Feature Flag
SHOW_DOLLAR = True

# Script Configuration
FUNCTIONS = {
    "calculate_portfolio": ("calculate_portfolio.py", PORT_API),
    "visualize_portfolio": ("visualize_portfolio.py", PORT_PORTFOLIO),
    "visualize_budget": ("visualize_budget.py", PORT_BUDGET)
}

def kill_port(port):
    """
    Kill any process using the specified port.

    Args:
        port (int): The port to free up.
    """
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    proc.kill()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

def open_browser(port):
    """
    Automatically open the Dash app in a web browser.

    Args:
        port (int): The port the app is running on.
    """
    webbrowser.open_new(f"http://127.0.0.1:{port}")

def run_function(script_name, port, show_dollar):
    """
    Run the selected script in a new tab with the feature flag.

    Args:
        script_name (str): The script to execute.
        port (int): The port the script will run on.
        show_dollar (bool): Feature flag for showing dollar values.
    """
    kill_port(port)
    os.system(f"python3 {script_name} --show-dollar {str(show_dollar)} &")

def main():
    """
    Create and run the Dash app for selecting and running scripts.
    """
    global SHOW_DOLLAR
    kill_port(PORT_MAIN)
    app = Dash(__name__)

    # App Layout
    app.layout = html.Div(
        style=DEFAULT_STYLE,
        children=[
            html.H1("Main Menu", style={"textAlign": "center", "fontSize": "24px"}),
            html.Hr(),

            # Feature Flag Section
            html.Div(
                [
                    html.Label(
                        id="feature_flag_label",
                        style={"fontSize": "16px", "fontWeight": "bold", "marginRight": "10px"},
                    ),
                    html.H3(),
                    html.Button(
                        id="feature_flag_button",
                        n_clicks=0,
                        style={"margin": "10px"},
                    ),
                    html.Hr(),
                ],
                style={"textAlign": "center", "marginBottom": "20px"},
            ),

            # Script Buttons
            html.Div(
                [
                    html.Button(
                        "Calculate Portfolio",
                        id="calculate_portfolio",
                        n_clicks=0,
                        style={"margin": "10px"},
                    ),
                    html.Button(
                        "Visualize Portfolio",
                        id="visualize_portfolio",
                        n_clicks=0,
                        style={"margin": "10px"},
                    ),
                    html.Button(
                        "Visualize Budget",
                        id="visualize_budget",
                        n_clicks=0,
                        style={"margin": "10px"},
                    ),
                ],
                style={"textAlign": "center"},
            ),

            # Output Section
            html.Div(
                id="output",
                style={"textAlign": "center", "marginTop": "20px", "fontSize": "16px"},
            ),
        ],
    )

    # Callback: Toggle Feature Flag
    @app.callback(
        [Output("feature_flag_label", "children"),
         Output("feature_flag_button", "children")],
        Input("feature_flag_button", "n_clicks"),
    )
    def toggle_feature_flag(n_clicks):
        """
        Toggle the feature flag and update label and button text.

        Args:
            n_clicks (int): Number of times the button has been clicked.

        Returns:
            Tuple[str, str]: Updated label and button text.
        """
        global SHOW_DOLLAR
        SHOW_DOLLAR = n_clicks % 2 == 0
        label_text = "Balance Visible" if SHOW_DOLLAR else "Balance Hidden"
        button_text = "Hide" if SHOW_DOLLAR else "Show"
        return label_text, button_text

    # Callback: Handle Button Clicks
    @app.callback(
        Output("output", "children"),
        [Input("calculate_portfolio", "n_clicks"),
         Input("visualize_portfolio", "n_clicks"),
         Input("visualize_budget", "n_clicks")],
    )
    def handle_button_click(calc_clicks, vis_port_clicks, vis_budget_clicks):
        """
        Handle button clicks and run the corresponding script.

        Args:
            calc_clicks (int): Clicks for the "Calculate Portfolio" button.
            vis_port_clicks (int): Clicks for the "Visualize Portfolio" button.
            vis_budget_clicks (int): Clicks for the "Visualize Budget" button.

        Returns:
            str: Status message indicating the action taken.
        """
        triggered = callback_context.triggered

        if not triggered:
            return "No action taken yet."

        button_id = triggered[0]["prop_id"].split(".")[0]

        if button_id in FUNCTIONS:
            script_name, port = FUNCTIONS[button_id]
            run_function(script_name, port, SHOW_DOLLAR)
            return f"Running {button_id.replace('_', ' ').title()}"

        return "Invalid action."

    # Automatically open the app in a browser
    Timer(1, open_browser, args=[PORT_MAIN]).start()

    # Run the app
    app.run_server(debug=True, use_reloader=False, port=PORT_MAIN)

if __name__ == "__main__":
    main()