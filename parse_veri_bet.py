import time
import json
import asyncio
from dataclasses import dataclass
from playwright.async_api import async_playwright


@dataclass
class Item:
    sport_league: str = ''
    event_date_utc: str = ''
    team1: str = ''
    team2: str = ''
    pitcher: str = ''
    period: str = ''
    line_type: str = ''
    price: str = ''
    side: str = ''
    team: str = ''
    spread: float = 0.0


async def fetch_page_data():
    # Launching Firefox browser
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)  # You can set headless=False to see the browser
        page = await browser.new_page()
        await page.goto('https://sportsbetting.dog/picks')  # Go directly to the picks page

        print("Page loaded.")

        # Wait for a certain element to ensure the page is loaded (adjust if needed)
        try:
            await page.wait_for_selector('.betting-lines', timeout=60000)  # Adjust the selector to a valid one
            print("Betting lines found!")

            # Get the HTML content of the page
            content = await page.content()
            await browser.close()

            return content
        except Exception as e:
            print(f"Error occurred while waiting for the betting lines: {e}")
            await browser.close()
            return None


def parse_event_lines(page_content):
    items = []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page_content, 'html.parser')

    # Locate the event rows with betting lines (make sure this selector is correct)
    event_rows = soup.find_all('div', class_='betRow')

    for row in event_rows:
        try:
            sport_league = row.find('div', class_='sport-name').get_text(strip=True)
            event_date_utc = row.find('div', class_='event-date').get('data-utc')
            team1 = row.find('div', class_='team1-name').get_text(strip=True)
            team2 = row.find('div', class_='team2-name').get_text(strip=True)

            # Iterate over different betting options (moneyline, spread, total, etc.)
            bet_rows = row.find_all('div', class_='betLine')
            for bet_row in bet_rows:
                line_type = bet_row.find('div', class_='line-type').get_text(strip=True)
                price = bet_row.find('div', class_='price').get_text(strip=True)
                side = bet_row.find('div', class_='side').get_text(strip=True)
                spread = bet_row.find('div', class_='spread').get_text(strip=True) if 'spread' in line_type.lower() else 0
                team = bet_row.find('div', class_='team').get_text(strip=True)
                period = bet_row.find('div', class_='period').get_text(strip=True)

                item = Item(
                    sport_league=sport_league,
                    event_date_utc=event_date_utc,
                    team1=team1,
                    team2=team2,
                    line_type=line_type,
                    price=price,
                    side=side,
                    team=team,
                    spread=float(spread)
                )
                items.append(item)

        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    return items


async def main():
    while True:
        try:
            page_content = await fetch_page_data()

            # Check if page content was retrieved successfully
            if page_content:
                items = parse_event_lines(page_content)
                items_json = json.dumps([item.__dict__ for item in items], indent=4)
                print(items_json)
            else:
                print("Failed to retrieve content.")

            # Wait before refreshing the data
            time.sleep(10)  # Adjust based on how often the data updates

        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
