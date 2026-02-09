# FPL Price Change Bot

A Telegram bot that posts daily Fantasy Premier League price changes at 9 AM UK time.

## Features

- 📈 **Daily Price Rises** — Lists all players whose price increased overnight
- 📉 **Daily Price Falls** — Lists all players whose price dropped
- 🕘 **Automated Schedule** — Posts automatically at 9:00 AM daily
- 💬 **Manual Commands** — `/pricechanges` to get updates on-demand

## How It Works

1. Fetches current player prices from the [FPL API](https://fantasy.premierleague.com/api/bootstrap-static/)
2. Compares to yesterday's prices stored in a [GitHub repo](https://github.com/meharpalbasi/fpl_price_change_daily)
3. Posts formatted messages to the Telegram channel

## Setup

### Prerequisites

- Python 3.8+
- A Telegram bot token (from [@BotFather](https://t.me/botfather))
- Access to the price history repo

### Installation

```bash
# Clone the repo
git clone https://github.com/meharpalbasi/telegram-bot.git
cd telegram-bot

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export API_KEY="your_telegram_bot_token"
```

### Configuration

Edit `main.py` to set your target channel/chat:

```python
CHAT_ID = -1002392242605  # Your Telegram channel/group ID
```

### Running

```bash
python main.py
```

The bot will:
- Start listening for commands (`/start`, `/pricechanges`)
- Run the scheduler to post at 9 AM daily

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/pricechanges` | Get current price changes immediately |

## Deployment

Deployed on [Railway](https://railway.app) with:
- `API_KEY` environment variable set
- Continuous running via `python main.py`

## Example Output

```
📈 Price Rises (5)

Salah (MID) - £13.0m → £13.1m (+£0.1m)
Palmer (MID) - £10.8m → £10.9m (+£0.1m)
...

📉 Price Falls (3)

Rashford (MID) - £7.2m → £7.1m (-£0.1m)
...
```

## Tech Stack

- **Language:** Python 3
- **Bot Framework:** pyTelegramBotAPI (telebot)
- **Scheduling:** schedule
- **Data:** pandas
- **Deployment:** Railway

## License

MIT
