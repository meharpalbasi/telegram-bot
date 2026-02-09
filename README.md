# FPL Price Change Bot

A Telegram bot that posts daily Fantasy Premier League updates to [@fplpricechanges](https://t.me/fplpricechanges).

## Features

### Live Now
- 📈 **Daily Price Rises** — Players whose price increased overnight
- 📉 **Daily Price Falls** — Players whose price dropped

### Planned Features
See [ROADMAP.md](ROADMAP.md) for upcoming features.

## How It Works

1. GitHub Action runs daily at 6am UTC
2. Fetches current prices from FPL API
3. Compares to yesterday's prices (from [fpl_price_change_daily](https://github.com/meharpalbasi/fpl_price_change_daily))
4. Sends formatted message to Telegram channel

## Setup

### Repository Secrets
Add these in Settings → Secrets → Actions:
- `TELEGRAM_API_KEY` — Bot token from [@BotFather](https://t.me/botfather)
- `TELEGRAM_CHAT_ID` — Channel username (e.g., `@fplpricechanges`)

### Manual Test
Actions tab → "Daily FPL Price Update" → "Run workflow"

## Files

- `send_update.py` — Main script that fetches data and sends Telegram message
- `.github/workflows/daily_price_update.yml` — Cron schedule (6am UTC daily)

## Tech Stack

- **Language:** Python 3.11
- **Data:** FPL API + pandas
- **Messaging:** pyTelegramBotAPI
- **Hosting:** GitHub Actions (free, no server needed)

## Related Projects

- [fpl_price_change_daily](https://github.com/meharpalbasi/fpl_price_change_daily) — Daily price snapshot
- [fpl-dbt-analytics](https://github.com/meharpalbasi/fpl-dbt-analytics) — Analytics pipeline
- [xPoints](https://github.com/meharpalbasi/xPoints) — Expected points model
- [fplanaly.st](https://fplanaly.st) — Web app

## License

MIT
