import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from modules.web_extraction_tools.product_reviews.call_for_single_product_review_selenium import navigate_to_reviews_selenium  # Import your function from call_for_single_product_review_selenium.py

class ReviewExtractor:
    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)

    def __del__(self):
        self.driver.quit()

    def extract_reviews_for_product(self, product_id):
        reviews_data = navigate_to_reviews_selenium(product_id, self.driver)
        return reviews_data

def main():
    st.title('Product Reviews Extractor')

    extractor = ReviewExtractor()

    product_id = st.text_input('Enter Product ID (e.g., 1VCE8):')

    if st.button('Extract Reviews'):
        if product_id:
            st.write(f"Extracting reviews for Product ID: {product_id}...")
            reviews_data = extractor.extract_reviews_for_product(product_id)
            if reviews_data:
                st.subheader('Extracted Reviews:')
                for idx, review in enumerate(reviews_data, start=1):
                    st.write(f"\nReview {idx}:")
                    st.write(f"Star Rating: {review['Star Rating']}")
                    st.write(f"Rating Text: {review['Rating Text']}")
                    st.write(f"Review Text: {review['Review Text']}")
            else:
                st.write("No reviews found for the given Product ID.")

if __name__ == '__main__':
    main()
