# Form 4 Insider Trading Tracker

A Python-based tool to track SEC Form 4 filings (insider buys and sales) for companies you're interested in. Monitor insider trading activity, transaction types, amounts, and other key details.

## Features

- **Automated Form 4 Fetching**: Automatically downloads and parses Form 4 filings from SEC Edgar
- **Watchlist Management**: Track multiple companies with a customizable watchlist
- **Transaction Parsing**: Extracts detailed transaction information including:
  - Transaction type (Open Market Purchase, Open Market Sale, Grant/Award, etc.)
  - Number of shares
  - Price per share
  - Total transaction value
  - Insider name and title
  - Transaction date
  - Shares owned after transaction
- **Buy/Sell Filtering**: Separate views for insider buys vs. sales
- **Summary Statistics**: Get quick insights into insider trading activity
- **Data Storage**: Stores all transactions locally for historical analysis

## What is Form 4?

Form 4 is an SEC filing that must be submitted by company insiders (officers, directors, and 10% shareholders) within two business days of buying or selling company stock. Tracking these filings can provide insights into insider sentiment about the company.

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd insider-buy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your watchlist and settings:
```bash
# Edit config.yaml to add your email and companies to track
nano config.yaml
```

## Configuration

Edit `config.yaml` to customize:

```yaml
# Add company tickers you want to track
watchlist:
  - AAPL    # Apple Inc.
  - MSFT    # Microsoft Corp.
  - TSLA    # Tesla Inc.

# SEC Edgar settings
sec:
  # Required: Your email for SEC API compliance
  user_agent: "YourName your.email@example.com"

  # How many days back to check for filings
  lookback_days: 7

# Data storage settings
storage:
  data_dir: "./data"
  save_raw_xml: true
```

**Important**: Update the `user_agent` field with your name and email. The SEC requires this for API access.

## Usage

### Update Form 4 Filings

Fetch the latest Form 4 filings for all companies in your watchlist:

```bash
python main.py update
```

Update for a specific ticker:

```bash
python main.py update --ticker AAPL
```

### View Insider Buys

Show all insider purchases:

```bash
python main.py buys
```

Show buys for a specific ticker in the last 30 days:

```bash
python main.py buys --ticker TSLA --days 30
```

### View Insider Sales

Show all insider sales:

```bash
python main.py sales
```

Show sales for a specific ticker:

```bash
python main.py sales --ticker NVDA --days 7
```

### View All Transactions

Show both buys and sales:

```bash
python main.py all --ticker AAPL --days 14
```

### View Summary Statistics

Get a summary of insider trading activity:

```bash
python main.py summary --ticker MSFT --days 7
```

Example output:
```
Summary for MSFT (Last 7 days)
========================================
Activity          Count    Shares    Total Value
--------------  -------  --------  -------------
Insider Buys          3    15,000       $5.25M
Insider Sales         1     5,000       $1.75M

Net Activity                            $3.50M

Unique Insiders Buying: 2
Unique Insiders Selling: 1
```

### Manage Watchlist

View your current watchlist:

```bash
python main.py watchlist
```

Add a ticker to watchlist:

```bash
python main.py watchlist --add NVDA
```

Remove a ticker from watchlist:

```bash
python main.py watchlist --remove NVDA
```

## Transaction Types

The tracker identifies various transaction types:

- **Open Market Purchase (P)**: Insider bought shares on the open market
- **Open Market Sale (S)**: Insider sold shares on the open market
- **Grant/Award (A)**: Shares granted as compensation
- **Exercise of Derivative (M)**: Insider exercised options
- **Payment of Exercise Price or Tax Liability (F)**: Shares sold to pay taxes
- And more...

## Data Storage

All data is stored locally in the `./data` directory:

- `filings.json`: Raw filing metadata and parsed data
- `transactions.json`: Individual transaction records
- `raw_xml/`: Original XML files (if `save_raw_xml: true`)

## Example Workflow

1. **Initial Setup**:
```bash
# Install dependencies
pip install -r requirements.txt

# Configure your email and watchlist in config.yaml
nano config.yaml
```

2. **Daily Usage**:
```bash
# Update filings each morning
python main.py update

# Check for insider buys
python main.py buys --days 1

# View summary for specific company
python main.py summary --ticker AAPL --days 7
```

3. **Research**:
```bash
# Find all buys in last 30 days for a stock
python main.py buys --ticker TSLA --days 30

# Compare buys vs sales
python main.py summary --ticker TSLA --days 30
```

## Understanding the Output

When viewing transactions, you'll see:

- **Ticker**: Stock symbol
- **Date**: Transaction date
- **Insider**: Name of the insider
- **Title**: Their role (CEO, Director, etc.)
- **Type**: Transaction type (Open Market Purchase, etc.)
- **Shares**: Number of shares traded
- **Price**: Price per share
- **Total Value**: Total transaction value

## Tips

1. **SEC Rate Limits**: The tool automatically throttles requests to comply with SEC limits (10 requests/second)

2. **Email Required**: The SEC requires contact information in the User-Agent. Update `config.yaml` with your email.

3. **Lookback Period**: Adjust `lookback_days` in config to control how far back to search. Longer periods mean more data but slower updates.

4. **Multiple Tickers**: You can track as many companies as you want in your watchlist.

5. **Data Persistence**: All data is stored locally and persists between runs. Rerunning `update` will fetch new filings without duplicating existing ones.

## Troubleshooting

**No data showing up?**
- Make sure you've run `python main.py update` first
- Check that your tickers are correct
- Verify your internet connection

**"User-Agent" error?**
- Update the `user_agent` field in `config.yaml` with your email

**Rate limit errors?**
- The tool should handle this automatically, but you can increase the delay between requests if needed

## Legal Disclaimer

This tool is for informational and educational purposes only. It is not investment advice. Always do your own research and consult with financial professionals before making investment decisions.

Form 4 data is public information provided by the SEC. This tool simply makes it easier to access and analyze.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

MIT License - See LICENSE file for details
