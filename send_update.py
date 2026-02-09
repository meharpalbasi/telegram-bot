#!/usr/bin/env python3
"""
One-shot script to send FPL price changes to Telegram.
Designed to be run by GitHub Actions cron.
"""
import os
import requests
import pandas as pd
import datetime
import telebot
import sys

# Configuration from environment
API_KEY = os.getenv('API_KEY')
CHAT_ID = os.getenv('CHAT_ID') or '-1002392242605'

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


def load_yesterday_costs():
    """Load yesterday's cost data from GitHub."""
    github_url = "https://raw.githubusercontent.com/meharpalbasi/fpl_price_change_daily/main/yesterday_costs.csv"
    
    try:
        response = requests.get(github_url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        print(f"Loaded {len(df)} records from yesterday's data")
        return df
    except Exception as e:
        print(f"Error loading yesterday's costs: {e}")
        return pd.DataFrame()


def format_price_changes(df, change_type):
    """Format price changes for Telegram message (matches main.py format)."""
    arrow = '🔽' if change_type == 'Price Falls' else '🔼'
    header = f"{change_type} {arrow}\n\n"
    subheader = "Player          New Price     Old Price\n"

    if df.empty:
        return header + "None"

    message_lines = []
    for _, player in df.iterrows():
        line = (
            f"{player['web_name']:<15}"
            f"£{player['now_cost']/10:<12.1f}"
            f"£{player['prev_cost']/10:.1f}"
        )
        message_lines.append(line)

    return header + subheader + "\n".join(message_lines)


def get_price_changes():
    """Get today's price changes."""
    players_df = fetch_fpl_data()
    yesterday_df = load_yesterday_costs()
    
    if yesterday_df.empty:
        return None, None, "Could not load yesterday's data"
    
    # Clean up today's data
    players_clean_df = players_df[["id", "web_name", "now_cost", "element_type"]].copy()
    players_clean_df["position"] = players_clean_df["element_type"].map(type_mapping)
    
    # Merge with yesterday
    merged_df = players_clean_df.merge(
        yesterday_df, on="id", how="left", suffixes=("", "_yest")
    )
    
    # Calculate daily change
    merged_df["daily_change"] = merged_df["now_cost"] - merged_df["now_cost_yest"]
    merged_df["prev_cost"] = merged_df["now_cost_yest"]
    
    # Filter changed players
    changed = merged_df[merged_df["daily_change"] != 0].copy()
    
    rises = changed[changed["daily_change"] > 0].sort_values("now_cost", ascending=False)
    falls = changed[changed["daily_change"] < 0].sort_values("now_cost", ascending=False)
    
    return rises, falls, None


def main():
    print(f"Sending FPL price update at {datetime.datetime.now()}")
    
    rises, falls, error = get_price_changes()
    
    if error:
        message = f"⚠️ FPL Price Update Error\n\n{error}"
    else:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        falls_msg = format_price_changes(falls, "Price Falls")
        rises_msg = format_price_changes(rises, "Price Rises")
        
        message = f"Price Changes for {today}\n\n{falls_msg}\n\n{'─' * 40}\n\n{rises_msg}"
    
    try:
        bot.send_message(CHAT_ID, message)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Failed to send message: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
