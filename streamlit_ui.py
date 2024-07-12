import logging
import sys
import uuid

import streamlit as st
import requests

st.title("Grainger Recommendations Chatbot")

backend_url = "http://localhost:8000"

# Initialize session
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())
    # response = requests.get(f"{backend_url}/initialize_session")
    # logging.info(f"backend_url: {backend_url}")
    # logging.info(f"session_id: {response.text}")
    # if response.status_code == 200:
    #     st.session_state.session_id = response.json().get("session_id")

# Ask a question
question = st.text_input("Enter your question:")
if st.button("Ask"):
    logging.info(f"Streamlit App pointing to {backend_url}")
    if st.session_state.session_id:
        response = requests.post(
            f"{backend_url}/ask_question",
            headers={"session-id": st.session_state.session_id},
            json={"question": question, "clear_history": False}
        )
        if response.status_code == 200:
            data = response.json()
            st.write("Response:", data["message"])
            st.write("Response JSON:", data["response_json"])
            st.write("Time taken:", data["time_taken"])
            st.write("Customer attributes retrieved:", data["customer_attributes_retrieved"])
            st.write("Time to get attributes:", data["time_to_get_attributes"])
        else:
            st.write("Error:", response.text)

# Fetch images
st.write("Fetch Images")
product_info = st.text_area("Enter product info as JSON list (e.g. [{'product': 'Product1', 'code': '12345'}])")
if st.button("Fetch Images"):
    try:
        products = eval(product_info)
        response = requests.post(
            f"{backend_url}/fetch_images",
            json=products
        )
        if response.status_code == 200:
            image_data_list = response.json()
            for image_data in image_data_list:
                st.image(image_data["image_data"], caption=image_data["code"])
        else:
            st.write("Error:", response.text)
    except Exception as e:
        st.write("Invalid JSON input:", str(e))

# Fetch reviews
st.write("Fetch Reviews")
# review_info = st.text_area("Enter product info as JSON list (e.g. [{'product': 'Product1', 'code': '12345'}])")
# if st.button("Fetch Reviews"):
#     try:
#         products = eval(review_info)
#         response = requests.post(
#             f"{backend_url}/fetch_reviews",
#             json=products
#         )
#         if response.status_code == 200:
#             reviews = response.json()
#             st.write(reviews)
#         else:
#             st.write("Error:", response.text)
#     except Exception as e:
#         st.write("Invalid JSON input:", str(e))
