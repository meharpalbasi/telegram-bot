#!/usr/bin/env python3
"""
Send daily transfer trends to Telegram.
Shows top transfers in/out for the current gameweek.
"""
import os
import requests
import datetime
import telebot
import sys

# Configuration
API_KEY = os.getenv('API_KEY')
CHAT_ID = os.getenv('CHAT_ID') or '@fplpricechanges'

if not API_KEY:
    print("ERROR: API_KEY environment variable not set")
    sys.exit(1)

bot = telebot.TeleBot(API_KEY)

FPL_API = 'https://fantasy.premierleague.com/api/bootstrap-static/'


def fetch_fpl_data():
    """Fetch FPL bootstrap data."""
    response = requests.get(FPL_API, timeout=30)
    response.raise_for_status()
    return response.json()


def format_number(n):
    """Format large numbers with K/M suffix."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def get_transfer_trends(data, top_n=10):
    """Get top transfers in and out."""
    players = data['elements']
    
    # Sort by transfers in (descending)
    top_in = sorted(players, key=lambda x: x['transfers_in_event'], reverse=True)[:top_n]
    
    # Sort by transfers out (descending)
    top_out = sorted(players, key=lambda x: x['transfers_out_event'], reverse=True)[:top_n]
    
    return top_in, top_out


def format_transfer_message(top_in, top_out):
    """Format the transfer trends message."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    lines = [f"📊 Transfer Trends - {today}", ""]
    
    # Top transfers in
    lines.append("🔥 Most Transferred IN")
    lines.append("")
    for i, p in enumerate(top_in, 1):
        net = p['transfers_in_event'] - p['transfers_out_event']
        net_str = f"+{format_number(net)}" if net > 0 else format_number(net)
        lines.append(
            f"{i}. {p['web_name']} — {format_number(p['transfers_in_event'])} in ({net_str} net)"
        )
    
    lines.append("")
    lines.append("─" * 30)
    lines.append("")
    
    # Top transfers out
    lines.append("📉 Most Transferred OUT")
    lines.append("")
    for i, p in enumerate(top_out, 1):
        net = p['transfers_in_event'] - p['transfers_out_event']
        net_str = f"+{format_number(net)}" if net > 0 else format_number(net)
        lines.append(
            f"{i}. {p['web_name']} — {format_number(p['transfers_out_event'])} out ({net_str} net)"
        )
    
    return "\n".join(lines)


def main():
    print(f"Sending transfer trends at {datetime.datetime.now()}")
    
    try:
        data = fetch_fpl_data()
        top_in, top_out = get_transfer_trends(data)
        message = format_transfer_message(top_in, top_out)
        
        bot.send_message(CHAT_ID, message)
        print("Message sent successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
