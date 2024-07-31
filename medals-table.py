from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def parse_table_from_visible_rows(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('div', {'data-testid': 'noc-row'})
    
    for row in rows:
        order_number = row.find('span', class_='e1oix8v91').text
        flag_img = row.find('img', class_='elhe7kv3')
        flag_url = flag_img['src'] if flag_img else 'N/A'
        country_code = row.find('span', class_='elhe7kv4').text
        country_name = row.find('span', class_='elhe7kv5').text
        medal_counts = row.find_all('span', class_='e1oix8v91 emotion-srm-81g9w1')
        gold = medal_counts[0].text if len(medal_counts) > 0 else '0'
        silver = medal_counts[1].text if len(medal_counts) > 1 else '0'
        bronze = medal_counts[2].text if len(medal_counts) > 2 else '0'
        total_medals_span = row.find('span', class_='e1oix8v91 emotion-srm-5nhv3o')
        total_medals = total_medals_span.text if total_medals_span else '0'

        print(f"Order: {order_number}")
        print(f"Flag URL: {flag_url}")
        print(f"Country Code: {country_code}")
        print(f"Country Name: {country_name}")
        print(f"Gold: {gold}, Silver: {silver}, Bronze: {bronze}")
        print(f"Total Medals: {total_medals}")
        print("---")

def main():
    chrome_options = Options()
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--headless=new")  # Run in headless mode 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    # Optional additional arguments
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--proxy-server='direct://'")
    # chrome_options.add_argument("--proxy-bypass-list=*")
    driver = webdriver.Chrome(options=chrome_options)

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
    main()

