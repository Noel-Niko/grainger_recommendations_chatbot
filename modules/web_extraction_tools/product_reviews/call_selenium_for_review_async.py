from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import asyncio
from selenium.webdriver.firefox.options import Options as FirefoxOptions


async def navigate_and_get_soup(driver, url):
    """Navigate to a URL and return the page's BeautifulSoup object."""
    await asyncio.to_thread(driver.get, url)
    # No need to sleep here; WebDriverWait will dynamically wait for elements
    return BeautifulSoup(driver.page_source, 'html.parser')


def extract_reviews(soup):
    """Extract review information from a BeautifulSoup object."""
    if not soup:
        print("No HTML content to process.")
        return []

    star_rating_values = []
    recommendation_percentages = []
    review_texts = []

    star_rating_container = soup.find('section', class_='pr-review-snapshot-block-snippet')
    if star_rating_container:
        star_rating_text = star_rating_container.find('div', class_='pr-snippet-rating-decimal').text.strip()
        try:
            star_rating_values.append(float(star_rating_text))
        except ValueError:
            pass

    recommendation_section = soup.find('section', class_='pr-review-snapshot-block-recommend')
    if recommendation_section:
        recommendation_percent_text = recommendation_section.find('span', class_='pr-reco-value').text.strip().replace(
            '%', '')
        try:
            recommendation_percentages.append(float(recommendation_percent_text))
        except ValueError:
            pass

    reviews = soup.find_all('section', class_='pr-rd-content-block')
    for review in reviews:
        review_text = review.find('p', class_='pr-rd-description-text')
        if review_text:
            review_texts.append(review_text.text.strip())

    avg_star_rating = sum(star_rating_values) / len(star_rating_values) if star_rating_values else None
    avg_recommendation_percent = sum(recommendation_percentages) / len(
        recommendation_percentages) if recommendation_percentages else None

    return {
        'Average Star Rating': avg_star_rating,
        'Average Recommendation Percent': avg_recommendation_percent,
        'Review Texts': review_texts
    }


async def async_navigate_to_reviews_selenium(product_id, driver):
    options = FirefoxOptions()
    options.headless = True

    search_url = f'https://www.zoro.com/search?q={product_id}'

    try:
        # Navigate to the search results page and wait for the product link to appear
        await navigate_and_get_soup(driver, search_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.product-card-image__link')))
        product_link = driver.find_element(By.CSS_SELECTOR, 'a.product-card-image__link')
        product_url = product_link.get_attribute('href')
    except TimeoutError:
        print("Product link not found within 10 seconds.")
        driver.quit()
        return []

    try:
        # Navigate directly to the product page and wait for the reviews link to appear
        await navigate_and_get_soup(driver, product_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="reviews"]')))
        reviews_link = driver.find_element(By.CSS_SELECTOR, 'a[href*="reviews"]')
        reviews_url = reviews_link.get_attribute('href')
    except TimeoutError:
        print("Reviews link not found within 10 seconds.")
        driver.quit()
        return []

    # Now, navigate to the reviews page and get the BeautifulSoup object for processing
    await navigate_and_get_soup(driver, reviews_url)

    # Extract reviews data from the BeautifulSoup object
    reviews_data = extract_reviews(await navigate_and_get_soup(driver, reviews_url))

    driver.quit()
    return reviews_data

# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# import asyncio
#
# async def async_navigate_to_reviews_selenium(product_id, driver):
#     async def get_page_soup(url):
#         await asyncio.to_thread(driver.get, url)
#         await asyncio.sleep(1)  # Wait for the page to load
#         return BeautifulSoup(driver.page_source, 'html.parser')
#
#     def extract_reviews(html_content):
#         if not html_content:
#             print("No HTML content to process.")
#             return []
#
#         soup = BeautifulSoup(html_content, 'html.parser')
#
#         # Extracting star ratings
#         star_rating_values = []
#         star_rating_container = soup.find('section', class_='pr-review-snapshot-block-snippet')
#         if star_rating_container:
#             star_rating_text = star_rating_container.find('div', class_='pr-snippet-rating-decimal').text.strip()
#             try:
#                 star_rating_values.append(float(star_rating_text))
#             except ValueError:
#                 pass
#
#         # Extracting recommendation percentages
#         recommendation_percentages = []
#         recommendation_section = soup.find('section', class_='pr-review-snapshot-block-recommend')
#         if recommendation_section:
#             recommendation_percent_text = recommendation_section.find('span', class_='pr-reco-value').text.strip().replace('%', '')
#             try:
#                 recommendation_percentages.append(float(recommendation_percent_text))
#             except ValueError:
#                 pass
#
#         # Extracting review texts
#         reviews = soup.find_all('section', class_='pr-rd-content-block')
#         review_texts = []
#
#         for review in reviews:
#             review_text = review.find('p', class_='pr-rd-description-text')
#             if review_text:
#                 review_texts.append(review_text.text.strip())
#
#         # Calculating averages
#         avg_star_rating = sum(star_rating_values) / len(star_rating_values) if star_rating_values else None
#         avg_recommendation_percent = sum(recommendation_percentages) / len(recommendation_percentages) if recommendation_percentages else None
#
#         return {
#             'Average Star Rating': avg_star_rating,
#             'Average Recommendation Percent': avg_recommendation_percent,
#             'Review Texts': review_texts
#         }
#
#     search_url = f'https://www.zoro.com/search?q={product_id}'
#     await asyncio.to_thread(driver.get, search_url)
#     await asyncio.sleep(1)  # Wait for the page to load
#
#     try:
#         await asyncio.to_thread(WebDriverWait(driver, 3).until, EC.presence_of_element_located((By.CSS_SELECTOR, 'a.product-card-image__link')))
#     except TimeoutError:
#         print("Product link not found within 3 seconds.")
#         return []
#
#     # Find the specific product link using CSS selector
#     product_link = await asyncio.to_thread(driver.find_element, By.CSS_SELECTOR, 'a.product-card-image__link')
#     product_url = await asyncio.to_thread(product_link.get_attribute, 'href')
#     await asyncio.to_thread(driver.get, product_url)
#     await asyncio.sleep(1)  # Wait for the product page to load
#
#     try:
#         await asyncio.to_thread(WebDriverWait(driver, 3).until, EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="reviews"]')))
#     except TimeoutError:
#         print("Reviews link not found within 3 seconds.")
#         return []
#
#     # Find the reviews link using CSS selector
#     reviews_link = await asyncio.to_thread(driver.find_element, By.CSS_SELECTOR, 'a[href*="reviews"]')
#     reviews_url = await asyncio.to_thread(reviews_link.get_attribute, 'href')
#     await asyncio.to_thread(driver.get, reviews_url)
#     await asyncio.sleep(1)  # Wait for the reviews page to load
#
#     html_content = driver.page_source
#
#     reviews_data = extract_reviews(html_content)
#
#     return reviews_data
#
# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.support.ui import WebDriverWait
# # from selenium.webdriver.support import expected_conditions as EC
# # from bs4 import BeautifulSoup
# # import asyncio
# #
# # async def async_navigate_to_reviews_selenium(product_id, driver):
# #     async def get_page_soup(url):
# #         await asyncio.to_thread(driver.get, url)
# #         await asyncio.sleep(1)  # Wait for the page to load
# #         return BeautifulSoup(driver.page_source, 'html.parser')
# #
# #     def extract_reviews(html_content):
# #         if not html_content:
# #             print("No HTML content to process.")
# #             return []
# #
# #         soup = BeautifulSoup(html_content, 'html.parser')
# #
# #         star_rating_label = None
# #         star_rating_text = None
# #         recommendation_percent = None
# #
# #         # Extracting star rating
# #         star_rating_container = soup.find('section', class_='pr-review-snapshot-block-snippet')
# #         if star_rating_container:
# #             star_rating = star_rating_container.find('div', class_='pr-snippet-stars')
# #             star_rating_text = star_rating_container.find('div', class_='pr-snippet-rating-decimal').text.strip()
# #             star_rating_label = star_rating['aria-label'] if star_rating else None
# #
# #         # Extracting recommendation percentage
# #         recommendation_section = soup.find('section', class_='pr-review-snapshot-block-recommend')
# #         if recommendation_section:
# #             recommendation_percent = recommendation_section.find('span', class_='pr-reco-value').text.strip()
# #
# #         # Extracting reviews
# #         reviews = soup.find_all('section', class_='pr-rd-content-block')
# #         reviews_data = []
# #
# #         for idx, review in enumerate(reviews, start=1):
# #             review_text = review.find('p', class_='pr-rd-description-text')
# #             reviews_data.append({
# #                 'Recommendation Percent': recommendation_percent,
# #                 'Star Rating': star_rating_label,
# #                 'Rating Text': star_rating_text,
# #                 'Review Text': review_text.text.strip() if review_text else None
# #             })
# #
# #         return reviews_data
# #
# #     search_url = f'https://www.zoro.com/search?q={product_id}'
# #     await asyncio.to_thread(driver.get, search_url)
# #     await asyncio.sleep(2)  # Wait for the page to load
# #
# #     try:
# #         await asyncio.to_thread(WebDriverWait(driver, 10).until, EC.presence_of_element_located((By.CSS_SELECTOR, 'a.product-card-image__link')))
# #     except TimeoutError:
# #         print("Product link not found within 10 seconds.")
# #         return []
# #
# #     # Find the specific product link using CSS selector
# #     product_link = await asyncio.to_thread(driver.find_element, By.CSS_SELECTOR, 'a.product-card-image__link')
# #     product_url = await asyncio.to_thread(product_link.get_attribute, 'href')
# #     await asyncio.to_thread(driver.get, product_url)
# #     await asyncio.sleep(2)  # Wait for the product page to load
# #
# #     try:
# #         await asyncio.to_thread(WebDriverWait(driver, 10).until, EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="reviews"]')))
# #     except TimeoutError:
# #         print("Reviews link not found within 10 seconds.")
# #         return []
# #
# #     # Find the reviews link using CSS selector
# #     reviews_link = await asyncio.to_thread(driver.find_element, By.CSS_SELECTOR, 'a[href*="reviews"]')
# #     reviews_url = await asyncio.to_thread(reviews_link.get_attribute, 'href')
# #     await asyncio.to_thread(driver.get, reviews_url)
# #     await asyncio.sleep(2)  # Wait for the reviews page to load
# #
# #     html_content = driver.page_source
# #
# #     reviews_data = extract_reviews(html_content)
# #
# #     return reviews_data
