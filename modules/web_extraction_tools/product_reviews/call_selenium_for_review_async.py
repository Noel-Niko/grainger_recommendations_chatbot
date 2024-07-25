import asyncio
import contextlib
import logging
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
tag = "call_selenium_for_review_async.py"


async def navigate_and_get_soup(driver, url):
    """Navigate to a URL and return the page's BeautifulSoup object."""
    await asyncio.to_thread(driver.get, url)
    # No need to sleep here; WebDriverWait will dynamically wait for elements
    return BeautifulSoup(driver.page_source, "html.parser")


def extract_reviews(soup):
    """Extract review information from a BeautifulSoup object."""
    if not soup:
        print("No HTML content to process.")
        return []

    star_rating_values = []
    recommendation_percentages = []
    review_texts = []

    star_rating_container = soup.find("section", class_="pr-review-snapshot-block-snippet")
    if star_rating_container:
        star_rating_text = star_rating_container.find("div", class_="pr-snippet-rating-decimal").text.strip()
        with contextlib.suppress(ValueError):
            star_rating_values.append(float(star_rating_text))

    recommendation_section = soup.find("section", class_="pr-review-snapshot-block-recommend")
    if recommendation_section:
        recommendation_percent_text = recommendation_section.find("span", class_="pr-reco-value").text.strip().replace("%", "")
        with contextlib.suppress(ValueError):
            recommendation_percentages.append(float(recommendation_percent_text))

    reviews = soup.find_all("section", class_="pr-rd-content-block")
    for review in reviews:
        review_text = review.find("p", class_="pr-rd-description-text")
        if review_text:
            review_texts.append(review_text.text.strip())

    avg_star_rating = sum(star_rating_values) / len(star_rating_values) if star_rating_values else None
    avg_recommendation_percent = sum(recommendation_percentages) / len(recommendation_percentages) if recommendation_percentages else None

    return {"Average Star Rating": avg_star_rating, "Average Recommendation Percent": avg_recommendation_percent, "Review Texts": review_texts}


async def async_navigate_to_reviews_selenium(product_id):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    running_in_docker = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"

    if running_in_docker:
        chrome_bin = os.getenv("CHROME_BIN", "/usr/local/bin/google-chrome")
        chrome_driver = os.getenv("CHROME_DRIVER", "/usr/local/bin/chromedriver")
        options.binary_location = chrome_bin
        service = Service(chrome_driver)
    else:
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    search_url = f"https://www.zoro.com/search?q={product_id}"

    try:
        # Navigate to the search results page and wait for the product link to appear
        soup = await navigate_and_get_soup(driver, search_url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.product-card-image__link")))
        product_link = driver.find_element(By.CSS_SELECTOR, "a.product-card-image__link")
        product_url = product_link.get_attribute("href")
    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"{tag} / Product link not found within the wait time. Error: {e}")
        return []
    except Exception as e:
        logging.error(f"{tag} / Unexpected error during product link navigation. Error: {e}")
        return []

    try:
        # Navigate directly to the product page and wait for the reviews link to appear
        soup = await navigate_and_get_soup(driver, product_url)
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="reviews"]')))
        reviews_link = driver.find_element(By.CSS_SELECTOR, 'a[href*="reviews"]')
        reviews_url = reviews_link.get_attribute("href")
    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"{tag} / Reviews link not found within the wait time. Error: {e}")
        return []
    except Exception as e:
        logging.error(f"{tag} / Unexpected error during reviews link navigation. Error: {e}")
        return []

    try:
        # Now, navigate to the reviews page and get the BeautifulSoup object for processing
        soup = await navigate_and_get_soup(driver, reviews_url)
        # Extract reviews data from the BeautifulSoup object
        reviews_data = extract_reviews(soup)
    except Exception as e:
        logging.error(f"{tag} / Unexpected error during reviews page navigation. Error: {e}")
        return []

    return reviews_data
