import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os
import schedule
import time

URL = 'https://www.bajus.org/gold-price'
CSV_FILE = 'output_filled.csv'

def fetch_gold_prices():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    response = requests.get(URL, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    tbody = soup.find('tbody')
    if not tbody:
        print("Could not find gold prices table.")
        return

    rows = tbody.find_all('tr')

    prices = {}

    for row in rows:
        title = row.find('h6')
        price_span = row.find('span', class_='price')

        if title and price_span:
            name = title.get_text(strip=True).lower()
            price_text = price_span.get_text(strip=True)
            price = int(price_text.split()[0].replace(',', ''))

            if '22 karat' in name:
                prices['k22'] = price
            elif '21 karat' in name:
                prices['k21'] = price
            elif '18 karat' in name:
                prices['k18'] = price
            elif 'traditional' in name:
                prices['traditional'] = price

    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')

    row = [
        date_str,
        prices.get('k18', ''),
        prices.get('k21', ''),
        prices.get('k22', ''),
        prices.get('traditional', '')
    ]

    print(f"Saving row: {row}")

    # Check if file exists
    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['date', 'k18', 'k21', 'k22', 'traditional'])  # Write header only once
        writer.writerow(row)

def job():
    print(f"Running scheduled job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    fetch_gold_prices()

# Schedule the job daily
schedule.every().day.at("10:00").do(job)

if __name__ == '__main__':
    print("Gold Price Bot Started...")
    while True:
        schedule.run_pending()
        time.sleep(60)
