# FPL Bot Roadmap

Planned features leveraging the FPL analytics ecosystem.

## Phase 1: Daily Updates (Next)

### Transfer Trends
- Top 10 transfers in/out today
- Net transfer delta
- Ownership % changes

### Price Predictions
- Players likely to rise tonight (high transfer in %)
- Players likely to fall tonight (high transfer out %)

## Phase 2: xPoints Integration

### Top xPoints Picks
- Top 5 players by position for upcoming GW
- Pull from [xPoints](https://github.com/meharpalbasi/xPoints) predictions

### Captain Picks
- Top 3 captain options
- xPoints + fixture difficulty combined score

### Differentials
- Low ownership (<10%) + high xPoints
- "Gems" for the week

## Phase 3: Gameweek-Timed Alerts

### Deadline Reminder
- 2 hours before GW deadline
- Include top captain pick
- "Make your transfers!"

### Fixture Ticker
- Teams with best next 5 fixtures
- Good time to target assets

## Phase 4: Post-Gameweek

### Top Performers
- Highest points this GW
- Bonus point leaders
- xPoints vs actual comparison

### Price Change Predictions
- End-of-day predictions for tonight's changes
- Based on ownership velocity

---

## Data Sources

| Feature | Source |
|---------|--------|
| Price changes | fpl_price_change_daily repo |
| xPoints | xPoints repo (predictions.json) |
| Fixtures/FDR | fpl-dbt-analytics API |
| Differentials | fpl-dbt-analytics /differentials |
| Transfer trends | FPL API bootstrap-static |

## Technical Notes

- All features run as GitHub Actions (no hosting costs)
- Each feature = separate workflow or combined into daily digest
- Use fpl-dbt-analytics FastAPI endpoints where possible
