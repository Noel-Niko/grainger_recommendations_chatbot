import requests
from bs4 import BeautifulSoup


def navigate_to_reviews(product_id):
    # Function to get HTML content from a URL
    def get_html(url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Failed to retrieve content from {url}. Status code: {response.status_code}")
            return None

    def extract_reviews(html_content):
        if not html_content:
            print("No HTML content to process.")
            return []

        soup = BeautifulSoup(html_content, "html.parser")

        # Extracting star rating
        star_rating_label = None
        star_rating_text = None
        star_rating_container = soup.find("section", class_="pr-review-snapshot-block-snippet")
        if star_rating_container:
            star_rating = star_rating_container.find("div", class_="pr-snippet-stars")
            star_rating_text = star_rating_container.find("div", class_="pr-snippet-rating-decimal").text.strip()
            star_rating_label = star_rating["aria-label"] if star_rating else None

        # Extracting recommendation percentage
        recommendation_section = soup.find("section", class_="pr-review-snapshot-block-recommend")
        if recommendation_section:
            recommendation_section.find("span", class_="pr-reco-value").text.strip()

        # Extracting reviews
        reviews = soup.find_all("section", class_="pr-rd-content-block")
        reviews_data = []
        for _idx, review in enumerate(reviews, start=1):
            review_text = review.find("p", class_="pr-rd-description-text")
            reviews_data.append(
                {"Star Rating": star_rating_label, "Rating Text": star_rating_text, "Review Text": review_text.text.strip() if review_text else None}
            )

        return reviews_data

    # Main
    search_url = f"https://www.zoro.com/search?q={product_id}"
    search_html = get_html(search_url)
    if not search_html:
        print(f"Failed to retrieve search results for {product_id}")
        return []

    soup = BeautifulSoup(search_html, "html.parser")
    product_link = soup.select_one("a.product-card-image__link")
    if not product_link:
        print(f"Product link not found for {product_id}")
        return []

    product_url = product_link["href"]
    product_html = get_html(product_url)
    if not product_html:
        print(f"Failed to retrieve product details for {product_id}")
        return []

    product_soup = BeautifulSoup(product_html, "html.parser")
    reviews_link = product_soup.select_one('a[href*="reviews"]')
    if not reviews_link:
        print(f"Reviews link not found for {product_id}")
        return []

    reviews_url = reviews_link["href"]
    reviews_html = get_html(reviews_url)
    if not reviews_html:
        print(f"Failed to retrieve reviews for {product_id}")
        return []

    reviews_data = extract_reviews(reviews_html)

    return reviews_data


# Example usage:
product_id = "1VCE8"
reviews_data = navigate_to_reviews(product_id)
if reviews_data:
    print("Reviews:")
    for idx, review in enumerate(reviews_data, start=1):
        print(f"\nReview {idx}:")
        print(f"Star Rating: {review['Star Rating']}")
        print(f"Rating Text: {review['Rating Text']}")
        print(f"Review Text: {review['Review Text']}")
else:
    print(f"No reviews found for product ID: {product_id}")
