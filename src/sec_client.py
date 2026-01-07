"""
SEC Edgar API Client for fetching Form 4 filings
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class SECClient:
    """Client for interacting with SEC Edgar API"""

    BASE_URL = "https://www.sec.gov"
    EDGAR_SEARCH_URL = f"{BASE_URL}/cgi-bin/browse-edgar"

    def __init__(self, user_agent: str):
        """
        Initialize SEC client

        Args:
            user_agent: User agent string (SEC requires email contact)
        """
        self.headers = {
            'User-Agent': user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_form4_filings(self, ticker: str, lookback_days: int = 7) -> List[Dict]:
        """
        Get Form 4 filings for a company ticker

        Args:
            ticker: Company ticker symbol
            lookback_days: Number of days to look back

        Returns:
            List of Form 4 filing metadata
        """
        filings = []

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        params = {
            'action': 'getcompany',
            'CIK': ticker,
            'type': '4',
            'dateb': end_date.strftime('%Y%m%d'),
            'owner': 'include',
            'count': '100'
        }

        try:
            # Rate limiting: SEC requests max 10 requests per second
            time.sleep(0.1)

            response = self.session.get(self.EDGAR_SEARCH_URL, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the filings table
            table = soup.find('table', {'class': 'tableFile2'})
            if not table:
                return filings

            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 5:
                    continue

                filing_type = cols[0].text.strip()
                if filing_type != '4':
                    continue

                filing_date = cols[3].text.strip()
                filing_date_obj = datetime.strptime(filing_date, '%Y-%m-%d')

                # Check if within date range
                if filing_date_obj < start_date:
                    continue

                # Get document link
                doc_link = cols[1].find('a', {'id': 'documentsbutton'})
                if not doc_link:
                    continue

                doc_url = self.BASE_URL + doc_link['href']

                filings.append({
                    'ticker': ticker,
                    'filing_type': filing_type,
                    'filing_date': filing_date,
                    'document_url': doc_url,
                    'accession_number': cols[4].text.strip()
                })

        except Exception as e:
            print(f"Error fetching Form 4 filings for {ticker}: {e}")

        return filings

    def get_form4_xml(self, document_url: str) -> Optional[str]:
        """
        Get the XML content of a Form 4 filing

        Args:
            document_url: URL to the filing documents page

        Returns:
            XML content as string, or None if error
        """
        try:
            # Rate limiting
            time.sleep(0.1)

            # Get the documents page
            response = self.session.get(document_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the XML document link
            table = soup.find('table', {'class': 'tableFile'})
            if not table:
                return None

            # Look for the primary Form 4 XML document
            # Priority:
            # 1. Document with type "4"
            # 2. First .xml file
            # 3. primary_doc.xml or wf-form4_*.xml

            xml_candidates = []

            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue

                # Get document info
                sequence = cols[0].text.strip() if len(cols) > 0 else ''
                description = cols[1].text.strip() if len(cols) > 1 else ''
                document = cols[2].text.strip() if len(cols) > 2 else ''
                doc_type = cols[3].text.strip() if len(cols) > 3 else ''

                link = cols[2].find('a')
                if not link:
                    continue

                # Check if this is the Form 4 XML
                is_form4_xml = False
                priority = 99

                if doc_type == '4':
                    is_form4_xml = True
                    priority = 0  # Highest priority
                elif document.endswith('.xml'):
                    is_form4_xml = True
                    if 'primary' in document.lower() or sequence == '1':
                        priority = 1
                    else:
                        priority = 2

                if is_form4_xml:
                    xml_candidates.append({
                        'url': self.BASE_URL + link['href'],
                        'priority': priority,
                        'document': document
                    })

            # Sort by priority and try to fetch
            xml_candidates.sort(key=lambda x: x['priority'])

            for candidate in xml_candidates:
                try:
                    # Fetch XML content
                    time.sleep(0.1)
                    xml_response = self.session.get(candidate['url'])
                    xml_response.raise_for_status()

                    content = xml_response.text

                    # Verify it's actually XML with ownershipDocument
                    if '<ownershipDocument>' in content or '<?xml' in content:
                        return content

                except Exception as e:
                    # Try next candidate
                    continue

        except Exception as e:
            print(f"Error fetching Form 4 XML: {e}")

        return None

    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK number for a company ticker

        Args:
            ticker: Company ticker symbol

        Returns:
            CIK number as string, or None if not found
        """
        try:
            params = {
                'action': 'getcompany',
                'CIK': ticker,
                'count': '1'
            }

            time.sleep(0.1)
            response = self.session.get(self.EDGAR_SEARCH_URL, params=params)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            cik_elem = soup.find('span', {'class': 'companyName'})

            if cik_elem:
                # CIK is in format: "COMPANY NAME (CIK#: 0000123456)"
                text = cik_elem.text
                if 'CIK#:' in text:
                    cik = text.split('CIK#:')[1].split(')')[0].strip()
                    return cik

        except Exception as e:
            print(f"Error getting CIK for {ticker}: {e}")

        return None
