"""
Main Form 4 Insider Trading Tracker
"""
import yaml
from typing import List, Dict, Optional
from .sec_client import SECClient
from .form4_parser import Form4Parser
from .data_manager import DataManager


class InsiderTracker:
    """Main tracker for Form 4 insider trading"""

    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize insider tracker

        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.client = SECClient(self.config['sec']['user_agent'])
        self.parser = Form4Parser()
        self.data_manager = DataManager(self.config['storage']['data_dir'])

    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_file}")
            print("Using default configuration")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration"""
        return {
            'watchlist': [],
            'sec': {
                'user_agent': 'Insider Tracker contact@example.com',
                'lookback_days': 7
            },
            'storage': {
                'data_dir': './data',
                'save_raw_xml': True
            }
        }

    def update_watchlist(self, tickers: Optional[List[str]] = None):
        """
        Fetch and update Form 4 filings for watchlist

        Args:
            tickers: List of ticker symbols to update (defaults to config watchlist)
        """
        watchlist = tickers or self.config.get('watchlist', [])
        lookback_days = self.config['sec']['lookback_days']

        if not watchlist:
            print("No tickers in watchlist. Please add tickers to config.yaml")
            return

        print(f"Updating Form 4 filings for {len(watchlist)} companies...")
        print(f"Looking back {lookback_days} days\n")

        total_filings = 0

        for ticker in watchlist:
            print(f"Fetching {ticker}...", end=' ')

            # Get Form 4 filings
            filings = self.client.get_form4_filings(ticker, lookback_days)

            if not filings:
                print("No recent filings")
                continue

            print(f"Found {len(filings)} filing(s)")

            # Process each filing
            for filing in filings:
                # Get XML content
                xml_content = self.client.get_form4_xml(filing['document_url'])

                if not xml_content:
                    print(f"  ⚠ Could not fetch XML for {filing['accession_number']}")
                    continue

                # Parse XML
                parsed_data = self.parser.parse(xml_content)

                if not parsed_data:
                    print(f"  ⚠ Could not parse XML for {filing['accession_number']}")
                    continue

                # Save to database
                self.data_manager.save_filing(filing, parsed_data)

                # Save raw XML if configured
                if self.config['storage'].get('save_raw_xml', False):
                    self._save_raw_xml(filing['accession_number'], xml_content)

                total_filings += 1

        print(f"\n✓ Updated {total_filings} Form 4 filing(s)")

    def _save_raw_xml(self, accession_number: str, xml_content: str):
        """Save raw XML file"""
        import os

        xml_dir = os.path.join(self.config['storage']['data_dir'], 'raw_xml')
        os.makedirs(xml_dir, exist_ok=True)

        filename = f"{accession_number.replace('-', '')}.xml"
        filepath = os.path.join(xml_dir, filename)

        with open(filepath, 'w') as f:
            f.write(xml_content)

    def get_transactions(self, ticker: Optional[str] = None, days: Optional[int] = None):
        """
        Get transactions

        Args:
            ticker: Filter by ticker
            days: Filter by days back

        Returns:
            DataFrame of transactions
        """
        return self.data_manager.get_transactions(ticker, days)

    def get_buys(self, ticker: Optional[str] = None, days: Optional[int] = None):
        """Get buy transactions"""
        return self.data_manager.get_insider_buys(ticker, days)

    def get_sales(self, ticker: Optional[str] = None, days: Optional[int] = None):
        """Get sale transactions"""
        return self.data_manager.get_insider_sales(ticker, days)

    def get_summary(self, ticker: Optional[str] = None, days: Optional[int] = 7):
        """Get summary statistics"""
        return self.data_manager.get_summary(ticker, days)

    def add_to_watchlist(self, ticker: str):
        """
        Add ticker to watchlist

        Args:
            ticker: Ticker symbol to add
        """
        if ticker.upper() not in [t.upper() for t in self.config.get('watchlist', [])]:
            self.config.setdefault('watchlist', []).append(ticker.upper())
            self._save_config()
            print(f"Added {ticker.upper()} to watchlist")
        else:
            print(f"{ticker.upper()} already in watchlist")

    def remove_from_watchlist(self, ticker: str):
        """
        Remove ticker from watchlist

        Args:
            ticker: Ticker symbol to remove
        """
        watchlist = self.config.get('watchlist', [])
        watchlist = [t for t in watchlist if t.upper() != ticker.upper()]
        self.config['watchlist'] = watchlist
        self._save_config()
        print(f"Removed {ticker.upper()} from watchlist")

    def _save_config(self):
        """Save configuration to file"""
        with open('config.yaml', 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
