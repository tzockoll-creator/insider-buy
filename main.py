#!/usr/bin/env python3
"""
Form 4 Insider Trading Tracker CLI
"""
import argparse
import sys
from tabulate import tabulate
from src.tracker import InsiderTracker


def format_currency(value):
    """Format value as currency"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.2f}K"
    else:
        return f"${value:.2f}"


def display_transactions(df, title="Transactions"):
    """Display transactions in a formatted table"""
    if df.empty:
        print(f"\nNo {title.lower()} found")
        return

    # Select and format columns
    columns = [
        'ticker',
        'transaction_date',
        'insider_name',
        'insider_title',
        'transaction_type',
        'shares',
        'price_per_share',
        'total_value'
    ]

    display_df = df[columns].copy()

    # Format values
    display_df['shares'] = display_df['shares'].apply(lambda x: f"{x:,.0f}")
    display_df['price_per_share'] = display_df['price_per_share'].apply(lambda x: f"${x:.2f}")
    display_df['total_value'] = display_df['total_value'].apply(format_currency)

    # Rename columns for display
    display_df.columns = [
        'Ticker',
        'Date',
        'Insider',
        'Title',
        'Type',
        'Shares',
        'Price',
        'Total Value'
    ]

    print(f"\n{title}")
    print("=" * 80)
    print(tabulate(display_df, headers='keys', tablefmt='grid', showindex=False))


def display_summary(summary):
    """Display summary statistics"""
    print(f"\nSummary for {summary['ticker']} (Last {summary['period_days']} days)")
    print("=" * 60)

    data = [
        ["Insider Buys", summary['total_buys'], f"{summary['buy_shares']:,.0f}", format_currency(summary['buy_value'])],
        ["Insider Sales", summary['total_sales'], f"{summary['sale_shares']:,.0f}", format_currency(summary['sale_value'])],
        ["", "", "", ""],
        ["Net Activity", "", "", format_currency(summary['net_value'])],
    ]

    headers = ["Activity", "Count", "Shares", "Total Value"]
    print(tabulate(data, headers=headers, tablefmt='grid'))

    print(f"\nUnique Insiders Buying: {summary['unique_insiders_buying']}")
    print(f"Unique Insiders Selling: {summary['unique_insiders_selling']}")


def cmd_update(tracker, args):
    """Update Form 4 filings"""
    tickers = [args.ticker] if args.ticker else None
    tracker.update_watchlist(tickers)


def cmd_buys(tracker, args):
    """Show insider buys"""
    df = tracker.get_buys(args.ticker, args.days)
    display_transactions(df, "Insider Buys")


def cmd_sales(tracker, args):
    """Show insider sales"""
    df = tracker.get_sales(args.ticker, args.days)
    display_transactions(df, "Insider Sales")


def cmd_all(tracker, args):
    """Show all transactions"""
    df = tracker.get_transactions(args.ticker, args.days)
    display_transactions(df, "All Transactions")


def cmd_summary(tracker, args):
    """Show summary"""
    summary = tracker.get_summary(args.ticker, args.days)
    display_summary(summary)


def cmd_watchlist(tracker, args):
    """Manage watchlist"""
    if args.add:
        tracker.add_to_watchlist(args.add)
    elif args.remove:
        tracker.remove_from_watchlist(args.remove)
    else:
        # Show current watchlist
        watchlist = tracker.config.get('watchlist', [])
        if watchlist:
            print("\nCurrent Watchlist:")
            for ticker in watchlist:
                print(f"  - {ticker}")
        else:
            print("\nWatchlist is empty")
            print("Add tickers with: python main.py watchlist --add TICKER")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Form 4 Insider Trading Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update filings for all watchlist companies
  python main.py update

  # Update for specific ticker
  python main.py update --ticker AAPL

  # Show recent insider buys
  python main.py buys --days 30

  # Show insider buys for specific ticker
  python main.py buys --ticker TSLA --days 7

  # Show summary
  python main.py summary --ticker NVDA

  # Manage watchlist
  python main.py watchlist
  python main.py watchlist --add AAPL
  python main.py watchlist --remove AAPL
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update Form 4 filings')
    update_parser.add_argument('--ticker', help='Specific ticker to update')

    # Buys command
    buys_parser = subparsers.add_parser('buys', help='Show insider buys')
    buys_parser.add_argument('--ticker', help='Filter by ticker')
    buys_parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')

    # Sales command
    sales_parser = subparsers.add_parser('sales', help='Show insider sales')
    sales_parser.add_argument('--ticker', help='Filter by ticker')
    sales_parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')

    # All transactions command
    all_parser = subparsers.add_parser('all', help='Show all transactions')
    all_parser.add_argument('--ticker', help='Filter by ticker')
    all_parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')

    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show summary statistics')
    summary_parser.add_argument('--ticker', help='Ticker symbol')
    summary_parser.add_argument('--days', type=int, default=7, help='Days to summarize (default: 7)')

    # Watchlist command
    watchlist_parser = subparsers.add_parser('watchlist', help='Manage watchlist')
    watchlist_parser.add_argument('--add', help='Add ticker to watchlist')
    watchlist_parser.add_argument('--remove', help='Remove ticker from watchlist')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize tracker
    tracker = InsiderTracker()

    # Execute command
    commands = {
        'update': cmd_update,
        'buys': cmd_buys,
        'sales': cmd_sales,
        'all': cmd_all,
        'summary': cmd_summary,
        'watchlist': cmd_watchlist
    }

    if args.command in commands:
        try:
            commands[args.command](tracker, args)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
