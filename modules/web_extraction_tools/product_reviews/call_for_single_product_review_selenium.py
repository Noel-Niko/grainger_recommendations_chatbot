import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def navigate_to_reviews_selenium(product_id):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Function to navigate to the reviews section of a product
    def get_page_soup(url):
        driver.get(url)
        time.sleep(1)  # Wait for the page to load
        return BeautifulSoup(driver.page_source, 'html.parser')

    def extract_reviews(html_content):
        if not html_content:
            print("No HTML content to process.")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')

        # Extracting star rating
        star_rating_container = soup.find('section', class_='pr-review-snapshot-block-snippet')
        if star_rating_container:
            star_rating = star_rating_container.find('div', class_='pr-snippet-stars')
            star_rating_text = star_rating_container.find('div', class_='pr-snippet-rating-decimal').text.strip()
            star_rating_label = star_rating['aria-label'] if star_rating else None
        else:
            star_rating_label = None
            star_rating_text = None

        # Extracting recommendation percentage
        recommendation_section = soup.find('section', class_='pr-review-snapshot-block-recommend')
        recommendation_percent = recommendation_section.find("span", class_="pr-reco-value").text.strip() if recommendation_section else None

        # Extracting reviews
        reviews = soup.find_all('section', class_='pr-rd-content-block')
        reviews_data = []

        for _idx, review in enumerate(reviews, start=1):
            review_text = review.find('p', class_='pr-rd-description-text')
            reviews_data.append({
                'Recommendation Percentage': recommendation_percent,
                'Star Rating': star_rating_label,
                'Rating Text': star_rating_text,
                'Review Text': review_text.text.strip() if review_text else None
            })

        return reviews_data

    # Main
    search_url = f'https://www.zoro.com/search?q={product_id}'
    driver.get(search_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.product-card-image__link')))
    except TimeoutError:
        print("Product link not found within 10 seconds.")
        return []

    # Find the specific product link using CSS selector
    product_link = driver.find_element(By.CSS_SELECTOR, 'a.product-card-image__link')
    product_url = product_link.get_attribute('href')
    driver.get(product_url)
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="reviews"]')))
    except TimeoutError:
        print("Reviews link not found within 3 seconds.")
        return []

    # Find the reviews link using CSS selector
    reviews_link = driver.find_element(By.CSS_SELECTOR, 'a[href*="reviews"]')
    reviews_url = reviews_link.get_attribute('href')
    driver.get(reviews_url)
    time.sleep(1)  # Wait for the reviews page to load

    html_content = driver.page_source

    reviews_data = extract_reviews(html_content)

    return reviews_data
