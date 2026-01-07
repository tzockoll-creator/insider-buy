#!/usr/bin/env python3
"""
Test script to examine Form 4 XML structure
"""
from src.sec_client import SECClient
from src.form4_parser import Form4Parser
from lxml import etree
import json

# Initialize client
client = SECClient("Test test@example.com")

# Get a recent filing for MSFT
print("Fetching recent MSFT Form 4 filings...")
filings = client.get_form4_filings("MSFT", lookback_days=30)

if not filings:
    print("No filings found")
    exit(1)

print(f"Found {len(filings)} filings\n")

# Get the first filing's XML
filing = filings[0]
print(f"Filing date: {filing['filing_date']}")
print(f"Accession: {filing['accession_number']}")
print(f"URL: {filing['document_url']}\n")

print("Fetching XML...")
xml_content = client.get_form4_xml(filing['document_url'])

if not xml_content:
    print("Could not fetch XML")
    exit(1)

print(f"XML length: {len(xml_content)} characters\n")

# Save raw XML for inspection
with open('test_form4.xml', 'w', encoding='utf-8') as f:
    f.write(xml_content)
print("Saved raw XML to: test_form4.xml\n")

# Parse and show structure
print("="*60)
print("PARSING XML")
print("="*60)

parser = etree.XMLParser(recover=True, remove_blank_text=True)
root = etree.fromstring(xml_content.encode('utf-8'), parser)

print(f"\nRoot tag: {root.tag}")
print(f"\nDirect children of root:")
for child in root:
    print(f"  - {child.tag}")

# Check for transaction tables
non_deriv = root.find('.//nonDerivativeTable')
deriv = root.find('.//derivativeTable')

print(f"\nnonDerivativeTable found: {non_deriv is not None}")
if non_deriv is not None:
    print(f"  Children:")
    for child in non_deriv:
        print(f"    - {child.tag}")
        if 'Transaction' in child.tag or 'Holding' in child.tag:
            print(f"      (has {len(list(child))} sub-elements)")

print(f"\nderivativeTable found: {deriv is not None}")
if deriv is not None:
    print(f"  Children:")
    for child in deriv:
        print(f"    - {child.tag}")
        if 'Transaction' in child.tag or 'Holding' in child.tag:
            print(f"      (has {len(list(child))} sub-elements)")

# Try parsing with our parser
print("\n" + "="*60)
print("PARSING WITH Form4Parser")
print("="*60)

parsed = Form4Parser.parse(xml_content)

if parsed:
    print(f"\nParsed successfully!")
    print(f"Issuer: {parsed['issuer']}")
    print(f"Owner: {parsed['reporting_owner']}")
    print(f"Non-derivative transactions: {len(parsed['non_derivative_transactions'])}")
    print(f"Derivative transactions: {len(parsed['derivative_transactions'])}")

    if parsed['non_derivative_transactions']:
        print(f"\nFirst non-derivative transaction:")
        print(json.dumps(parsed['non_derivative_transactions'][0], indent=2))

    if parsed['derivative_transactions']:
        print(f"\nFirst derivative transaction:")
        print(json.dumps(parsed['derivative_transactions'][0], indent=2))
else:
    print("\nParsing failed!")

print("\n" + "="*60)
