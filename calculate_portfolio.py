import pandas as pd
import requests
from datetime import datetime
from utils import (
    ALPHA_VANTAGE_API_KEY,
    INPUT_FILE,
    TEMP_FILE,
    LONG_TERM_HOLD_YEARS
)

def get_price(ticker, asset_type):
    """
    Fetch the current price for a given asset type using Alpha Vantage API.

    Args:
        ticker (str): The asset ticker symbol.
        asset_type (str): The type of asset (e.g., stock, etf, crypto, etc.).

    Returns:
        float: The current price of the asset, or 0 if there's an error.
    """
    if asset_type in ["cash", "401k", "hsa", "espp"]:
        return 1

    url, params = None, None
    if asset_type in ["stock", "etf"]:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
    elif asset_type == "crypto":
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": ticker.upper(),
            "to_currency": "USD",
            "apikey": ALPHA_VANTAGE_API_KEY,
        }
    else:
        print(f"Unsupported asset type: {asset_type}")
        return None

    response = requests.get(url, params=params)
    data = response.json()

    try:
        if asset_type in ["stock", "etf"]:
            return float(data["Global Quote"]["05. price"])
        elif asset_type == "crypto":
            return float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
    except KeyError:
        print(f"Error fetching price for {ticker} ({asset_type}). Response: {data}")
        return 0

def calculate_portfolio(input_file, output_file):
    """
    Process a portfolio CSV file, fetch current prices, and calculate stats.

    Args:
        input_file (str): Path to the input CSV file containing the portfolio.
        output_file (str): Path to save the processed portfolio CSV.
    """
    # Load portfolio data
    portfolio = pd.read_csv(input_file)

    if portfolio.empty:
        print("Portfolio is empty. Check your CSV file.")
        return

    # Initialize columns
    portfolio['Type'] = portfolio['Type'].fillna('').astype(str).str.lower()
    portfolio['Liquidity'] = portfolio['Liquidity'].fillna('').astype(str).str.lower()
    portfolio['Current Price'] = 0
    portfolio['Value'] = 0
    portfolio['Gain/Loss'] = 0
    portfolio['% Gain/Loss'] = 0
    portfolio['Long-Term Hold'] = ''

    total_value = 0

    for index, row in portfolio.iterrows():
        ticker = row['Ticker']
        asset_type = row['Type']
        quantity = row['Quantity']
        cost_basis = row.get('Cost Basis', 0)
        purchase_date = row.get('Purchase Date', '')

        if pd.isna(ticker) or pd.isna(asset_type) or pd.isna(quantity):
            print(f"Skipping row {index} due to missing data: {row}")
            continue

        # Handle different asset types
        if asset_type == "cash":
            price, value, gain_loss, percentage_gain_loss = 1, quantity, 0, 0
        elif asset_type in ["401k", "hsa"]:
            price = 1
            value = price * quantity
            gain_loss = value - cost_basis
            percentage_gain_loss = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 100
        else:
            price = get_price(ticker, asset_type)
            if price is None:
                print(f"Unknown asset type for {ticker}. Skipping.")
                continue
            value = price * quantity
            gain_loss = value - (cost_basis * quantity) if cost_basis > 0 else value
            percentage_gain_loss = (gain_loss / (cost_basis * quantity)) * 100 if cost_basis > 0 else 100

        total_value += value

        # Determine long-term hold status
        if not pd.isna(purchase_date):
            try:
                purchase_date_obj = datetime.strptime(str(purchase_date), "%Y-%m-%d")
                hold_duration_years = (datetime.now() - purchase_date_obj).days / 365
                long_term_hold = "Green" if hold_duration_years > LONG_TERM_HOLD_YEARS else "Red"
            except ValueError:
                long_term_hold = "Invalid Date"
        else:
            long_term_hold = "No Date"

        # Update portfolio data
        portfolio.at[index, 'Current Price'] = price
        portfolio.at[index, 'Value'] = value
        portfolio.at[index, 'Gain/Loss'] = gain_loss
        portfolio.at[index, '% Gain/Loss'] = percentage_gain_loss
        portfolio.at[index, 'Long-Term Hold'] = long_term_hold

    # Save updated portfolio
    portfolio.to_csv(output_file, index=False)
    print(f"Portfolio saved to {output_file}")

if __name__ == "__main__":
    calculate_portfolio(INPUT_FILE, TEMP_FILE)