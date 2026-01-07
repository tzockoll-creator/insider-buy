"""
Data manager for storing and retrieving Form 4 data
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class DataManager:
    """Manages storage and retrieval of Form 4 data"""

    def __init__(self, data_dir: str = "./data"):
        """
        Initialize data manager

        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = data_dir
        self.filings_file = os.path.join(data_dir, "filings.json")
        self.transactions_file = os.path.join(data_dir, "transactions.json")

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Initialize data files
        self._init_data_files()

    def _init_data_files(self):
        """Initialize data files if they don't exist"""
        if not os.path.exists(self.filings_file):
            with open(self.filings_file, 'w') as f:
                json.dump([], f)

        if not os.path.exists(self.transactions_file):
            with open(self.transactions_file, 'w') as f:
                json.dump([], f)

    def save_filing(self, filing_metadata: Dict, parsed_data: Dict):
        """
        Save a Form 4 filing

        Args:
            filing_metadata: Metadata about the filing
            parsed_data: Parsed Form 4 data
        """
        # Load existing filings
        filings = self._load_json(self.filings_file)

        # Check if filing already exists
        accession_number = filing_metadata.get('accession_number', '')
        existing = [f for f in filings if f.get('accession_number') == accession_number]

        if not existing:
            # Add new filing
            filing_record = {
                **filing_metadata,
                'parsed_data': parsed_data,
                'saved_at': datetime.now().isoformat()
            }
            filings.append(filing_record)
            self._save_json(self.filings_file, filings)

            # Save transactions
            self._save_transactions(filing_metadata, parsed_data)

    def _save_transactions(self, filing_metadata: Dict, parsed_data: Dict):
        """Save individual transactions from a filing"""
        transactions = self._load_json(self.transactions_file)

        issuer = parsed_data.get('issuer', {})
        owner = parsed_data.get('reporting_owner', {})
        filing_date = filing_metadata.get('filing_date', '')

        # Save non-derivative transactions
        for txn in parsed_data.get('non_derivative_transactions', []):
            transaction_record = {
                'ticker': issuer.get('ticker', ''),
                'company': issuer.get('name', ''),
                'filing_date': filing_date,
                'insider_name': owner.get('name', ''),
                'insider_title': owner.get('officer_title', ''),
                'is_director': owner.get('is_director', False),
                'is_officer': owner.get('is_officer', False),
                'transaction_date': txn.get('transaction_date', ''),
                'transaction_code': txn.get('transaction_code', ''),
                'transaction_type': txn.get('transaction_type', ''),
                'security_title': txn.get('security_title', ''),
                'shares': txn.get('shares', 0),
                'price_per_share': txn.get('price_per_share', 0),
                'total_value': txn.get('total_value', 0),
                'acquired_disposed': txn.get('acquired_disposed', ''),
                'shares_owned_after': txn.get('shares_owned_after', 0),
                'direct_indirect': txn.get('direct_indirect', ''),
                'is_derivative': False,
                'accession_number': filing_metadata.get('accession_number', ''),
                'saved_at': datetime.now().isoformat()
            }
            transactions.append(transaction_record)

        # Save derivative transactions
        for txn in parsed_data.get('derivative_transactions', []):
            transaction_record = {
                'ticker': issuer.get('ticker', ''),
                'company': issuer.get('name', ''),
                'filing_date': filing_date,
                'insider_name': owner.get('name', ''),
                'insider_title': owner.get('officer_title', ''),
                'is_director': owner.get('is_director', False),
                'is_officer': owner.get('is_officer', False),
                'transaction_date': txn.get('transaction_date', ''),
                'transaction_code': txn.get('transaction_code', ''),
                'transaction_type': txn.get('transaction_type', ''),
                'security_title': txn.get('security_title', ''),
                'shares': txn.get('shares', 0),
                'price_per_share': txn.get('price_per_share', 0),
                'total_value': txn.get('total_value', 0),
                'underlying_security': txn.get('underlying_security', ''),
                'underlying_shares': txn.get('underlying_shares', 0),
                'exercise_date': txn.get('exercise_date', ''),
                'expiration_date': txn.get('expiration_date', ''),
                'is_derivative': True,
                'accession_number': filing_metadata.get('accession_number', ''),
                'saved_at': datetime.now().isoformat()
            }
            transactions.append(transaction_record)

        self._save_json(self.transactions_file, transactions)

    def get_transactions(self, ticker: Optional[str] = None, days: Optional[int] = None) -> pd.DataFrame:
        """
        Get transactions as DataFrame

        Args:
            ticker: Filter by ticker symbol
            days: Filter by number of days back

        Returns:
            DataFrame of transactions
        """
        transactions = self._load_json(self.transactions_file)

        if not transactions:
            return pd.DataFrame()

        df = pd.DataFrame(transactions)

        # Filter by ticker
        if ticker:
            df = df[df['ticker'] == ticker.upper()]

        # Filter by days
        if days:
            cutoff_date = (datetime.now() - pd.Timedelta(days=days)).strftime('%Y-%m-%d')
            df = df[df['transaction_date'] >= cutoff_date]

        # Sort by transaction date (most recent first)
        if not df.empty and 'transaction_date' in df.columns:
            df = df.sort_values('transaction_date', ascending=False)

        return df

    def get_insider_buys(self, ticker: Optional[str] = None, days: Optional[int] = None) -> pd.DataFrame:
        """
        Get insider buy transactions

        Args:
            ticker: Filter by ticker symbol
            days: Filter by number of days back

        Returns:
            DataFrame of buy transactions
        """
        df = self.get_transactions(ticker, days)

        if df.empty:
            return df

        # Filter for purchases (P = Open Market Purchase, A = Award, etc.)
        buy_codes = ['P', 'A', 'M', 'X']
        df = df[df['transaction_code'].isin(buy_codes)]

        return df

    def get_insider_sales(self, ticker: Optional[str] = None, days: Optional[int] = None) -> pd.DataFrame:
        """
        Get insider sale transactions

        Args:
            ticker: Filter by ticker symbol
            days: Filter by number of days back

        Returns:
            DataFrame of sale transactions
        """
        df = self.get_transactions(ticker, days)

        if df.empty:
            return df

        # Filter for sales (S = Open Market Sale, D = Sale to Issuer, F = Tax Payment)
        sale_codes = ['S', 'D', 'F']
        df = df[df['transaction_code'].isin(sale_codes)]

        return df

    def get_summary(self, ticker: Optional[str] = None, days: Optional[int] = 7) -> Dict:
        """
        Get summary statistics

        Args:
            ticker: Filter by ticker symbol
            days: Number of days to summarize

        Returns:
            Dictionary with summary statistics
        """
        buys = self.get_insider_buys(ticker, days)
        sales = self.get_insider_sales(ticker, days)

        return {
            'period_days': days,
            'ticker': ticker or 'All',
            'total_buys': len(buys),
            'total_sales': len(sales),
            'buy_value': buys['total_value'].sum() if not buys.empty else 0,
            'sale_value': sales['total_value'].sum() if not sales.empty else 0,
            'buy_shares': buys['shares'].sum() if not buys.empty else 0,
            'sale_shares': sales['shares'].sum() if not sales.empty else 0,
            'net_value': (buys['total_value'].sum() if not buys.empty else 0) - (sales['total_value'].sum() if not sales.empty else 0),
            'unique_insiders_buying': buys['insider_name'].nunique() if not buys.empty else 0,
            'unique_insiders_selling': sales['insider_name'].nunique() if not sales.empty else 0
        }

    def _load_json(self, filepath: str) -> List:
        """Load JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, filepath: str, data: List):
        """Save JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def clear_data(self):
        """Clear all stored data"""
        self._save_json(self.filings_file, [])
        self._save_json(self.transactions_file, [])
