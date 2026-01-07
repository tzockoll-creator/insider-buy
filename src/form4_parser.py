"""
Parser for SEC Form 4 XML filings
"""
from typing import List, Dict, Optional
from datetime import datetime
from lxml import etree
import re


class Form4Parser:
    """Parser for Form 4 XML documents"""

    @staticmethod
    def parse(xml_content: str) -> Optional[Dict]:
        """
        Parse Form 4 XML content

        Args:
            xml_content: XML string content

        Returns:
            Dictionary with parsed Form 4 data, or None if error
        """
        try:
            # Clean up the XML content
            xml_content = Form4Parser._clean_xml(xml_content)

            # Parse XML using lxml with recovery mode
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            root = etree.fromstring(xml_content.encode('utf-8'), parser)

            # Extract issuer information
            issuer = Form4Parser._parse_issuer(root)

            # Extract reporting owner information
            reporting_owner = Form4Parser._parse_reporting_owner(root)

            # Extract non-derivative transactions
            non_derivative_transactions = Form4Parser._parse_non_derivative_transactions(root)

            # Extract derivative transactions
            derivative_transactions = Form4Parser._parse_derivative_transactions(root)

            return {
                'issuer': issuer,
                'reporting_owner': reporting_owner,
                'non_derivative_transactions': non_derivative_transactions,
                'derivative_transactions': derivative_transactions,
                'parsed_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error parsing Form 4 XML: {e}")
            return None

    @staticmethod
    def _parse_issuer(root) -> Dict:
        """Parse issuer (company) information"""
        issuer = {}

        issuer_elem = root.find('.//issuer')
        if issuer_elem is not None:
            name = issuer_elem.find('issuerName')
            cik = issuer_elem.find('issuerCik')
            ticker = issuer_elem.find('issuerTradingSymbol')

            issuer['name'] = name.text if name is not None else ''
            issuer['cik'] = cik.text if cik is not None else ''
            issuer['ticker'] = ticker.text if ticker is not None else ''

        return issuer

    @staticmethod
    def _parse_reporting_owner(root) -> Dict:
        """Parse reporting owner (insider) information"""
        owner = {}

        owner_elem = root.find('.//reportingOwner')
        if owner_elem is not None:
            owner_id = owner_elem.find('.//rptOwnerCik')
            owner_name = owner_elem.find('.//rptOwnerName')

            owner['cik'] = owner_id.text if owner_id is not None else ''
            owner['name'] = owner_name.text if owner_name is not None else ''

            # Relationship to company
            relationship = owner_elem.find('.//reportingOwnerRelationship')
            if relationship is not None:
                owner['is_director'] = Form4Parser._get_bool(relationship, 'isDirector')
                owner['is_officer'] = Form4Parser._get_bool(relationship, 'isOfficer')
                owner['is_ten_percent_owner'] = Form4Parser._get_bool(relationship, 'isTenPercentOwner')
                owner['is_other'] = Form4Parser._get_bool(relationship, 'isOther')

                officer_title = relationship.find('officerTitle')
                owner['officer_title'] = officer_title.text if officer_title is not None else ''

        return owner

    @staticmethod
    def _parse_non_derivative_transactions(root) -> List[Dict]:
        """Parse non-derivative transactions (actual stock buys/sells)"""
        transactions = []

        table = root.find('.//nonDerivativeTable')
        if table is None:
            return transactions

        for txn_elem in table.findall('.//nonDerivativeTransaction'):
            txn = Form4Parser._parse_single_transaction(txn_elem)
            if txn:
                transactions.append(txn)

        return transactions

    @staticmethod
    def _parse_derivative_transactions(root) -> List[Dict]:
        """Parse derivative transactions (options, warrants, etc.)"""
        transactions = []

        table = root.find('.//derivativeTable')
        if table is None:
            return transactions

        for txn_elem in table.findall('.//derivativeTransaction'):
            txn = Form4Parser._parse_single_derivative_transaction(txn_elem)
            if txn:
                transactions.append(txn)

        return transactions

    @staticmethod
    def _parse_single_transaction(txn_elem) -> Optional[Dict]:
        """Parse a single non-derivative transaction"""
        try:
            txn = {}

            # Security title
            security = txn_elem.find('.//securityTitle/value')
            txn['security_title'] = security.text if security is not None else ''

            # Transaction date
            txn_date = txn_elem.find('.//transactionDate/value')
            txn['transaction_date'] = txn_date.text if txn_date is not None else ''

            # Transaction code (P=Purchase, S=Sale, A=Award, etc.)
            txn_code = txn_elem.find('.//transactionCoding/transactionCode')
            txn['transaction_code'] = txn_code.text if txn_code is not None else ''
            txn['transaction_type'] = Form4Parser._get_transaction_type(txn['transaction_code'])

            # Deemed execution date (if different from transaction date)
            deemed_date = txn_elem.find('.//deemedExecutionDate/value')
            txn['deemed_execution_date'] = deemed_date.text if deemed_date is not None else ''

            # Transaction amounts
            shares = txn_elem.find('.//transactionAmounts/transactionShares/value')
            price = txn_elem.find('.//transactionAmounts/transactionPricePerShare/value')
            acquired_disposed = txn_elem.find('.//transactionAmounts/transactionAcquiredDisposedCode/value')

            txn['shares'] = float(shares.text) if shares is not None and shares.text else 0
            txn['price_per_share'] = float(price.text) if price is not None and price.text else 0
            txn['acquired_disposed'] = acquired_disposed.text if acquired_disposed is not None else ''

            # Calculate total value
            txn['total_value'] = txn['shares'] * txn['price_per_share']

            # Post-transaction amounts
            shares_owned = txn_elem.find('.//postTransactionAmounts/sharesOwnedFollowingTransaction/value')
            txn['shares_owned_after'] = float(shares_owned.text) if shares_owned is not None and shares_owned.text else 0

            # Ownership nature
            direct_indirect = txn_elem.find('.//ownershipNature/directOrIndirectOwnership/value')
            txn['direct_indirect'] = direct_indirect.text if direct_indirect is not None else 'D'

            # Transaction form type
            form_type = txn_elem.find('.//transactionCoding/transactionFormType')
            txn['form_type'] = form_type.text if form_type is not None else '4'

            return txn

        except Exception as e:
            print(f"Error parsing transaction: {e}")
            return None

    @staticmethod
    def _parse_single_derivative_transaction(txn_elem) -> Optional[Dict]:
        """Parse a single derivative transaction"""
        try:
            txn = {}

            # Security title
            security = txn_elem.find('.//securityTitle/value')
            txn['security_title'] = security.text if security is not None else ''

            # Transaction date
            txn_date = txn_elem.find('.//transactionDate/value')
            txn['transaction_date'] = txn_date.text if txn_date is not None else ''

            # Transaction code
            txn_code = txn_elem.find('.//transactionCoding/transactionCode')
            txn['transaction_code'] = txn_code.text if txn_code is not None else ''
            txn['transaction_type'] = Form4Parser._get_transaction_type(txn['transaction_code'])

            # Transaction amounts
            shares = txn_elem.find('.//transactionAmounts/transactionShares/value')
            price = txn_elem.find('.//transactionAmounts/transactionPricePerShare/value')

            txn['shares'] = float(shares.text) if shares is not None and shares.text else 0
            txn['price_per_share'] = float(price.text) if price is not None and price.text else 0
            txn['total_value'] = txn['shares'] * txn['price_per_share']

            # Exercise/conversion details
            exercise_date = txn_elem.find('.//exerciseDate/value')
            expiration_date = txn_elem.find('.//expirationDate/value')
            conversion_price = txn_elem.find('.//conversionOrExercisePrice/value')

            txn['exercise_date'] = exercise_date.text if exercise_date is not None else ''
            txn['expiration_date'] = expiration_date.text if expiration_date is not None else ''
            txn['conversion_price'] = float(conversion_price.text) if conversion_price is not None and conversion_price.text else 0

            # Underlying security
            underlying_security = txn_elem.find('.//underlyingSecurity/underlyingSecurityTitle/value')
            underlying_shares = txn_elem.find('.//underlyingSecurity/underlyingSecurityShares/value')

            txn['underlying_security'] = underlying_security.text if underlying_security is not None else ''
            txn['underlying_shares'] = float(underlying_shares.text) if underlying_shares is not None and underlying_shares.text else 0

            txn['is_derivative'] = True

            return txn

        except Exception as e:
            print(f"Error parsing derivative transaction: {e}")
            return None

    @staticmethod
    def _get_transaction_type(code: str) -> str:
        """Convert transaction code to readable type"""
        codes = {
            'P': 'Open Market Purchase',
            'S': 'Open Market Sale',
            'A': 'Grant/Award',
            'D': 'Sale to Issuer',
            'F': 'Payment of Exercise Price or Tax Liability',
            'I': 'Discretionary Transaction',
            'M': 'Exercise of Derivative',
            'C': 'Conversion of Derivative',
            'E': 'Expiration of Short Derivative',
            'H': 'Expiration of Long Derivative',
            'O': 'Exercise of Out-of-the-Money Derivative',
            'X': 'Exercise of In-the-Money Derivative',
            'G': 'Gift',
            'L': 'Small Acquisition',
            'W': 'Acquisition or Disposition by Will or Laws of Descent',
            'Z': 'Deposit into or Withdrawal from Voting Trust',
            'J': 'Other',
            'K': 'Transaction in Equity Swap',
            'U': 'Disposition to Beneficiary of Reporting Person'
        }
        return codes.get(code, f'Unknown ({code})')

    @staticmethod
    def _get_bool(element, tag: str) -> bool:
        """Get boolean value from XML element"""
        elem = element.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip() == '1' or elem.text.strip().lower() == 'true'
        return False

    @staticmethod
    def _clean_xml(xml_content: str) -> str:
        """
        Clean up XML content to handle SEC formatting issues

        Args:
            xml_content: Raw XML string

        Returns:
            Cleaned XML string
        """
        # Remove XML declaration if present (sometimes causes issues)
        xml_content = re.sub(r'<\?xml[^>]*\?>', '', xml_content)

        # Remove any HTML wrapper (SEC sometimes wraps XML in HTML)
        # Look for ownershipDocument tag which is the root of Form 4 XML
        match = re.search(r'<ownershipDocument>.*</ownershipDocument>', xml_content, re.DOTALL)
        if match:
            xml_content = match.group(0)

        # Add XML declaration back with proper encoding
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content

        # Replace &nbsp; and other HTML entities that might cause issues
        xml_content = xml_content.replace('&nbsp;', ' ')
        xml_content = xml_content.replace('&amp;', '&')

        # Remove any whitespace before the XML declaration
        xml_content = xml_content.strip()

        return xml_content
