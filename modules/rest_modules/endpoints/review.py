import asyncio
import logging
import traceback
from asyncio import Semaphore

import selenium
import selenium.common
from fastapi import APIRouter, HTTPException, Request

from modules.web_extraction_tools.product_reviews.call_selenium_for_review_async import async_navigate_to_reviews_selenium

router = APIRouter()
tag = "fast_api_main"

@router.post("/fetch_reviews")
async def fetch_reviews(request: Request):
    logging.info(f"{tag}/ Received request to fetch reviews.")
    try:
        products = await request.json()
        logging.info(f"{tag}/ Received products for review fetching: {products}")

        review_tasks = [fetch_review_for_product(product) for product in products]
        reviews = await asyncio.gather(*review_tasks)
        reviews = [review for review in reviews if review is not None]

        logging.info(f"{tag}/ Completed review fetching for all products.")
        return {"status": "completed", "reviews": reviews}
    except Exception as e:
        logging.error(f"{tag}/ Error fetching reviews: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error fetching reviews") from e


async def fetch_review_for_product(product):
    semaphore = Semaphore(10)
    async with semaphore:
        product_info = f"{product['product']}, {product['code']}"
        logging.info(f"{tag}/ Fetching reviews for product: {product_info}")

        try:
            reviews_data = await async_navigate_to_reviews_selenium(product_info)
        except selenium.common.exceptions.TimeoutException as e:
            logging.error(f"{tag}/ TimeoutException navigating to reviews for {product_info}: {str(e)}")
            return None
        except selenium.common.exceptions.NoSuchElementException as e:
            logging.error(f"{tag}/ NoSuchElementError navigating to reviews for {product_info}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"{tag}/ Error navigating to reviews for {product_info}: {str(e)}")
            logging.error(f"Stacktrace: {traceback.format_exc()}")
            return None

        if reviews_data:
            review = {
                "code": product['code'],
                "average_star_rating": reviews_data['Average Star Rating'],
                "average_recommendation_percent": reviews_data['Average Recommendation Percent'],
                "review_texts": reviews_data['Review Texts']
            }
            logging.info(f"{tag}/ Reviews for product {product['code']}: {reviews_data}")
            return review
        else:
            logging.info(f"{tag}/ No reviews found for product {product['code']}")
            return None
