from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
import sqlite3
import time
from webdriver_manager.firefox import GeckoDriverManager


DATABASE_NAME = 'medals.db'
MEDAL_TABLE_URL = 'https://olympics.com/en/paris-2024/medals'


def create_medals_table():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
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
    cursor.execute('''
        INSERT OR REPLACE INTO medals (order_number, flag_url, country_code, country_name, gold, silver, bronze, total_medals)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_number, flag_url, country_code, country_name, gold, silver, bronze, total_medals))
    conn.commit()
    conn.close()


def parse_table_from_visible_rows(content):
    '''
    Extracts visible medal table data from official olympics website
    and inserts the data into SQLite table
    '''
    soup = BeautifulSoup(content, 'html.parser')
    rows = soup.find_all('div', {'data-testid': 'noc-row'})
    
    for row in rows:
        order_number = int(row.find('span', class_='e1oix8v91').text)
        flag_img = row.find('img', class_='elhe7kv3')
        flag_url = flag_img['src'] if flag_img else ''
        country_code = row.find('span', class_='elhe7kv4').text
        country_name = row.find('span', class_='elhe7kv5').text
        medal_counts = row.find_all('span', class_='e1oix8v91 emotion-srm-81g9w1')
        gold = int(medal_counts[0].text) if len(medal_counts) > 0 else 0
        silver = int(medal_counts[1].text) if len(medal_counts) > 1 else 0
        bronze = int(medal_counts[2].text) if len(medal_counts) > 2 else 0
        total_medals = int(row.find('span', class_='e1oix8v91 emotion-srm-5nhv3o').text)
        insert_or_update_data(order_number, flag_url, country_code, country_name, gold, silver, bronze, total_medals)


def create_webdriver():
    options = webdriver.FirefoxOptions()
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("-headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage") # Disable shared memory usage

    # Proxy settings
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "")
    options.set_preference("network.proxy.socks_port", 0)
    options.set_preference("network.proxy.socks_remote_dns", False)
    install = GeckoDriverManager().install()
    return webdriver.Firefox(service=FirefoxService(install), options=options)


def create_table():
    create_medals_table()
    driver = create_webdriver()

    driver.get(MEDAL_TABLE_URL) # Open the url
    time.sleep(1) # HACK: Wait for the initial content to load

    # Continuously scroll and extract data from webpage until we reach the end...
    # HACK: We scroll downwards in viewport_height//5 increments and sleep for 100ms before
    #       continuing the next incremental scroll
    max_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    last_height = driver.execute_script("return window.pageYOffset + window.innerHeight")
    while last_height < max_height:
        parse_table_from_visible_rows(driver.page_source)

        # Scroll down by a fraction of the height of the viewport
        driver.execute_script(f"window.scrollBy(0, {viewport_height//5});")
        time.sleep(0.1) # HACK: Ensure content has loaded
        last_height = driver.execute_script("return window.pageYOffset + window.innerHeight")

    # Ensure we wcroll to the bottom, sleep then parse any remaining content
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.1) # HACK: Ensure content has loaded
    parse_table_from_visible_rows(driver.page_source)

    driver.quit()


def print_all_rows():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
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


if __name__ == "__main__":
    try:
        create_table()
    except sqlite3.Error as e:
        print(f'ERROR: Failed to create medals table: {e}')
        exit(1)
    print_all_rows()

