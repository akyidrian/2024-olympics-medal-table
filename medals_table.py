from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
import sqlite3
from webdriver_manager.firefox import GeckoDriverManager


DATABASE_NAME = 'medal_table.db'


def create_sqlite_table():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # TODO: try-catch
    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medals (
            order_number INTEGER,
            flag_url TEXT,
            country_code TEXT PRIMARY KEY,
            country_name TEXT,
            gold INTEGER,
            silver INTEGER,
            bronze INTEGER,
            total_medals INTEGER,
            FOREIGN KEY (country_name) REFERENCES population (entity)
            FOREIGN KEY (country_code) REFERENCES population (code)
        )
    ''')
    conn.commit()
    conn.close()


def insert_or_update_data(order_number, flag_url, country_code, country_name, gold, silver, bronze, total_medals):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO medals (order_number, flag_url, country_code, country_name, gold, silver, bronze, total_medals)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_number, flag_url, country_code, country_name, gold, silver, bronze, total_medals))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting {country_name} ({country_code}: {e}")
    finally:
        conn.close() # TODO: COMMIT?


def print_all_rows():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # TODO: try-catch?
    cursor.execute('''
        SELECT m.*,
               COALESCE(p1.population, p2.population) AS population
        FROM medals m
        LEFT JOIN population p1 ON m.country_name = p1.entity
        LEFT JOIN population p2 ON m.country_code = p2.code
    ''')
    rows = cursor.fetchall()
    
    for row in rows:
        print(row)
    print(f"Total medal winning countries: {len(rows)}")

    conn.close()

# TODO: Think there is a bug here
def parse_table_from_visible_rows(html_content):
    '''
    Extracts visible medal table data from official olympics website
    and inserts the data into SQLite table
    '''
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('div', {'data-testid': 'noc-row'})
    
    for row in rows:
        order_number = int(row.find('span', class_='e1oix8v91').text)
        flag_img = row.find('img', class_='elhe7kv3')
        flag_url = flag_img['src'] if flag_img else 'N/A'
        country_code = row.find('span', class_='elhe7kv4').text
        country_name = row.find('span', class_='elhe7kv5').text
        medal_counts = row.find_all('span', class_='e1oix8v91 emotion-srm-81g9w1')
        gold = int(medal_counts[0].text) if len(medal_counts) > 0 else 0
        silver = int(medal_counts[1].text) if len(medal_counts) > 1 else 0
        bronze = int(medal_counts[2].text) if len(medal_counts) > 2 else 0
        total_medals_span = row.find('span', class_='e1oix8v91 emotion-srm-5nhv3o')
        total_medals = int(total_medals_span.text) if total_medals_span else 0

        # Insert data into the SQLite table
        insert_or_update_data(order_number, flag_url, country_code, country_name, gold, silver, bronze, total_medals)

def create_table():
    create_sqlite_table()
    # Set up Firefox options
    options = webdriver.FirefoxOptions()

    # Set user agent
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Run in headless mode
    options.add_argument("-headless")

    # Set window size
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

    # Disable GPU (not typically needed for Firefox, but included for completeness)
    options.add_argument("--disable-gpu")

    # No sandbox (Firefox doesn't use sandboxing, so this is not applicable)

    # Disable shared memory usage
    options.add_argument("--disable-dev-shm-usage")

    # Proxy settings
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "")
    options.set_preference("network.proxy.socks_port", 0)
    options.set_preference("network.proxy.socks_remote_dns", False)
    install = GeckoDriverManager().install()
    driver = webdriver.Firefox(service=FirefoxService(install), options=options)

    try:
        # Open the URL
        driver.get('https://olympics.com/en/paris-2024/medals')

        # Wait for the initial content to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="noc-row"]')))

        # Scroll and extract data
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Extract data from currently visible rows
            html_content = driver.page_source
            parse_table_from_visible_rows(html_content)

            # Scroll down by the height of the viewport
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="noc-row"]')))
            
            # Check if we've reached the bottom of the page
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Ensure all content is loaded by scrolling to the bottom again and waiting
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="noc-row"]')))

        # Final extraction to ensure we got everything
        html_content = driver.page_source
        parse_table_from_visible_rows(html_content)

    finally:
        driver.quit()


if __name__ == "__main__":
    create_table()
    print_all_rows()

