import os
import requests
import pandas as pd
import datetime
import schedule
import time
import telebot
import threading

###################
#  CONFIGURATION  #
###################

# Telegram Bot Token (from BotFather). You can also read from environment variable if you prefer.
API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)

# The chat/group/channel ID to receive the daily message at 9 AM.
# If you want to auto-send to a private chat with yourself, 
# use your numeric user ID. For a group, use the group chat ID, etc.
CHAT_ID = -1002392242605

# FPL API endpoints
BASE_URL = 'https://fantasy.premierleague.com/api/'
GENERAL = 'bootstrap-static/'

# Mapping used to interpret element types and statuses
type_mapping = {
    1: "GK",
    2: "DEF",
    3: "MID",
    4: "FWD",
    'u': "Unavailable",
    'a': "Available",
    'd': "Doubtful",
    'NaN': "Info unavailable"
}


############################
#    PRICE CHANGE LOGIC    #
############################

def fetch_fpl_data():
    """Fetch the latest FPL data and return it as a pandas DataFrame."""
    url = BASE_URL + GENERAL
    r = requests.get(url).json()
    players_df = pd.DataFrame(r['elements'])
    return players_df

def load_yesterday_costs():
    """
    Load yesterday's cost data from GitHub private repository.
    Return an empty DataFrame if the file cannot be accessed.
    """
    # Use raw content URL
    github_url = "https://raw.githubusercontent.com/meharpalbasi/fpl_price_change_daily/main/yesterday_costs.csv"
    
    try:
        response = requests.get(github_url, verify=False)
        response.raise_for_status()
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        print(f"Loaded {len(df)} records from yesterday's data")
        print("Yesterday's data columns:", df.columns.tolist())
        return df
    except Exception as e:
        print(f"Error loading yesterday's costs: {e}")
        return pd.DataFrame()

def format_price_changes(df, change_type):
    """
    Return a formatted string listing the players who have
    changed price (up or down).
    """
    arrow = '🔽' if change_type == 'Price Falls' else '🔼'
    header = f"{change_type} {arrow}\n\n"
    subheader = "Player          New Price     Old Price\n"

    message_lines = []
    for _, player in df.iterrows():
        # We'll make columns aligned by using some spacing
        line = (
            f"{player['web_name']:<15}"     # left-aligned, 15 chars
            f"£{player['now_cost']/10:<12.1f}"
            f"£{player['prev_cost']/10:.1f}"
        )
        message_lines.append(line)

    # Combine lines with newlines
    body = "\n".join(message_lines)

    return header + subheader + body

def get_price_changes():
    """
    Encapsulates the logic to fetch data, merge with yesterday's costs,
    and return two strings: falls_message, rises_message.
    """
    # 1. Fetch today's data
    players_df = fetch_fpl_data()

    # 2. Load yesterday's data
    yesterday_df = load_yesterday_costs()

    if yesterday_df.empty:
        return "Warning: No 'yesterday_costs.csv' found.", ""

    # 3. Clean up today's data
    players_clean_df = players_df[["id", "web_name", "now_cost", "cost_change_event"]].assign(
        position=players_df['element_type'].map(type_mapping),
        availability=players_df['status'].map(type_mapping)
    )

    # 4. Merge with yesterday's data
    merged_df = players_clean_df.merge(
        yesterday_df,
        on="id",
        how="left",
        suffixes=("", "_yest")
    )

    # 5. Compute the daily change
    merged_df["daily_change"] = merged_df["now_cost"] - merged_df["now_cost_yest"]

    # 6. Create columns for new/previous cost
    merged_df["prev_cost"] = merged_df["now_cost_yest"]

    # 7. Filter out only players who changed price
    price_changed_players = merged_df[merged_df["daily_change"] != 0].copy()

    # 8. Arrow column (up/down)
    price_changed_players["arrow"] = price_changed_players["daily_change"].apply(
        lambda x: "up" if x > 0 else ("down" if x < 0 else "no_change")
    )

    # 9. Separate rises and falls
    price_rises = price_changed_players[price_changed_players["arrow"] == "up"]
    price_falls = price_changed_players[price_changed_players["arrow"] == "down"]

    # 10. Sort them
    price_rises = price_rises.sort_values(by='now_cost', ascending=True)
    price_falls = price_falls.sort_values(by='now_cost', ascending=True)

    # 11. Format the separate messages
    falls_message = format_price_changes(price_falls, 'Price Falls')
    rises_message = format_price_changes(price_rises, 'Price Rises')

    return falls_message, rises_message

def format_final_message(falls_message, rises_message):
    """
    Combine the two messages into one string, and include today's date.
    """
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    final_msg = (
        f"Price Changes for {today_str}\n\n"
        f"{falls_message}\n\n"
        "----------------------------------------\n\n"
        f"{rises_message}"
    )
    return final_msg

###############################
#   TELEGRAM BOT FUNCTIONS   #
###############################

@bot.message_handler(commands=['start'])
def handle_start(message):
    """
    Respond to /start command with a basic welcome message.
    """
    welcome_text = (
        "Hello! I'm your FPL Price Bot.\n"
        "Use /pricechanges to see today's FPL price updates."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['pricechanges'])
def handle_price_changes(message):
    """
    Respond to /pricechanges command by sending current price updates.
    """
    falls_message, rises_message = get_price_changes()
    
    # If the CSV is missing, just send that warning
    if "Warning:" in falls_message and not rises_message:
        bot.send_message(message.chat.id, falls_message)
        return
    
    # Otherwise send the combined, nicely formatted message
    final_msg = format_final_message(falls_message, rises_message)
    bot.send_message(message.chat.id, final_msg)

def send_price_update():
    """
    This function is called by the schedule at 9 AM.
    It fetches the price changes and sends them to a hardcoded CHAT_ID.
    """
    falls_message, rises_message = get_price_changes()
    
    # If no data (missing CSV), just warn the group or user
    if "Warning:" in falls_message and not rises_message:
        bot.send_message(CHAT_ID, falls_message)
        return
    
    final_msg = format_final_message(falls_message, rises_message)
    bot.send_message(CHAT_ID, final_msg)

###############################
#        SCHEDULER SETUP      #
###############################

# Schedule this script to send the message every day at 09:00
schedule.every().day.at("09:00").do(send_price_update)

def run_scheduler():
    """
    A simple loop that runs 'schedule.run_pending()' 
    to trigger the scheduled jobs (in a separate thread).
    """
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30s

if __name__ == "__main__":
    print("Starting the Scheduler and Bot. Press Ctrl+C to stop.")
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Start the bot (in main thread) - listens for /start, /pricechanges, etc.
    bot.infinity_polling()
