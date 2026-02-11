#!/usr/bin/env python3
"""
Price predictions: shows players most likely to rise/fall tonight.
Based on transfer velocity relative to ownership.
Runs at 5pm UK to give evening predictions before midnight price changes.
"""
import os
import requests
import pandas as pd
import datetime
import telebot
import sys

# Configuration from environment
API_KEY = os.getenv('API_KEY')
CHAT_ID = os.getenv('CHAT_ID', '-1002392242605')

if not API_KEY:
    print("ERROR: API_KEY environment variable not set")
    sys.exit(1)

bot = telebot.TeleBot(API_KEY)

# FPL API endpoints
BASE_URL = 'https://fantasy.premierleague.com/api/'
GENERAL = 'bootstrap-static/'

type_mapping = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
}


def fetch_fpl_data():
    """Fetch the latest FPL data."""
    url = BASE_URL + GENERAL
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json()['elements'])


def calculate_price_pressure(df):
    """
    Calculate 'price pressure' for each player.
    
    Price changes are triggered when transfers reach a threshold relative to ownership.
    We estimate pressure as: net_transfers / (ownership * total_players)
    
    Higher positive = more likely to rise
    Higher negative = more likely to fall
    """
    df = df.copy()
    
    # Get total managers from API (rough estimate if not available)
    total_managers = 10_000_000  # Approximate FPL managers
    
    # Convert selected_by_percent to numeric (sometimes comes as string)
    df['selected_by_percent'] = pd.to_numeric(df['selected_by_percent'], errors='coerce').fillna(0)
    
    # Calculate ownership as absolute number of owners
    df['owners'] = (df['selected_by_percent'] / 100) * total_managers
    
    # Net transfers this GW
    df['net_transfers'] = df['transfers_in_event'] - df['transfers_out_event']
    
    # Transfer velocity relative to ownership
    # Players with few owners need fewer transfers to change price
    # Use higher minimum to filter out low-ownership noise
    df['transfer_velocity'] = df['net_transfers'] / df['owners'].clip(lower=10000)
    
    # Separate rising and falling candidates
    # Only consider players with meaningful ownership (>0.1%)
    df['rising_pressure'] = df['transfers_in_event'] / df['owners'].clip(lower=10000)
    df['falling_pressure'] = df['transfers_out_event'] / df['owners'].clip(lower=10000)
    
    return df


def get_price_predictions():
    """Get players most likely to change price tonight."""
    try:
        players_df = fetch_fpl_data()
    except Exception as e:
        return None, None, f"Failed to fetch FPL data: {e}"
    
    # Add team names
    try:
        url = BASE_URL + GENERAL
        response = requests.get(url, timeout=30)
        teams = {t['id']: t['short_name'] for t in response.json()['teams']}
        players_df['team'] = players_df['team'].map(teams)
    except:
        players_df['team'] = ''
    
    # Calculate pressure metrics
    players_df = calculate_price_pressure(players_df)
    
    # Clean up for display
    players_df['position'] = players_df['element_type'].map(type_mapping)
    players_df['price'] = players_df['now_cost'] / 10
    
    # Filter to relevant columns
    cols = ['web_name', 'team', 'position', 'price', 
            'transfers_in_event', 'transfers_out_event', 'net_transfers',
            'selected_by_percent', 'rising_pressure', 'falling_pressure']
    
    analysis_df = players_df[cols].copy()
    
    # Filter to players with meaningful ownership (>0.1%) and transfer activity
    meaningful = analysis_df[analysis_df['selected_by_percent'] >= 0.1]
    
    # Top rising candidates (high net transfers in, relative to ownership)
    rising = meaningful[meaningful['net_transfers'] > 0].nlargest(10, 'rising_pressure')
    rising = rising[rising['transfers_in_event'] > 5000]  # Need significant activity
    
    # Top falling candidates (high net transfers out, relative to ownership)
    falling = meaningful[meaningful['net_transfers'] < 0].nlargest(10, 'falling_pressure')
    falling = falling[falling['transfers_out_event'] > 5000]  # Need significant activity
    
    return rising.head(5), falling.head(5), None


def format_predictions(df, direction):
    """Format predictions for Telegram."""
    emoji = '📈' if direction == 'rise' else '📉'
    header = f"Likely to {direction.upper()} tonight {emoji}\n\n"
    
    if df.empty:
        return header + "No strong predictions"
    
    lines = []
    for _, p in df.iterrows():
        net = f"+{int(p['net_transfers']):,}" if p['net_transfers'] > 0 else f"{int(p['net_transfers']):,}"
        lines.append(
            f"{p['web_name']} ({p['team']})\n"
            f"  £{p['price']:.1f} | {p['selected_by_percent']:.1f}% | Net: {net}"
        )
    
    return header + "\n\n".join(lines)


def main():
    print(f"Sending price predictions at {datetime.datetime.now()}")
    
    rising, falling, error = get_price_predictions()
    
    if error:
        message = f"⚠️ Price Prediction Error\n\n{error}"
    else:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        rising_msg = format_predictions(rising, "rise")
        falling_msg = format_predictions(falling, "fall")
        
        message = (
            f"🔮 Price Predictions for Tonight\n"
            f"─────────────────────────\n\n"
            f"{rising_msg}\n\n"
            f"{'─' * 30}\n\n"
            f"{falling_msg}\n\n"
            f"⏰ Prices update around 2:30am UK"
        )
    
    try:
        bot.send_message(CHAT_ID, message)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
