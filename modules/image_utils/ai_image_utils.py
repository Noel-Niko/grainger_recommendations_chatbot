import io
import json
import time
from base64 import b64decode
from tkinter import Image
import asyncio
import aiohttp
import pandas as pd
import time
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from IPython.core.display import display, HTML
import streamlit as st


async def generate_ai_thumbnail(rec_tuple, attributes, bedrock_runtime):
    rec, code = rec_tuple  # Unpack the tuple into rec (product description) and code

    gender_map = {
        'Womens': 'of a female ',
        'Mens': 'of a male '
    }

    prompt_parts = [
        f"Product view {gender_map.get(attributes.get('gender', ''))}in {rec}, dslr, ultra quality, dof, film grain, Fujifilm XT3, crystal clear, 8K UHD"
    ]

    # if attributes.get('environment'):
    #     prompt_parts.append(f", in a {attributes['environment']} setting")

    prompt_text = "".join(prompt_parts)

    request = json.dumps({
        "text_prompts": [
            {"text": prompt_text, "weight": 1.0},
            {"text": "poorly rendered", "weight": -1.0}
        ],
        "cfg_scale": 9,
        "seed": 4000,
        "steps": 50,
        "style_preset": "photographic",
    })
    modelId = "stability.stable-diffusion-xl-v1"

    start_time = time.time()
    response = await asyncio.to_thread(bedrock_runtime.invoke_model, body=request, modelId=modelId)
    response_body = json.loads(response.get("body").read())
    print(f"Thumbnail for recommendation '{rec}' generation completed in {time.time() - start_time:.2f} seconds.")

    base_64_img_str = response_body["artifacts"][0].get("base64")
    # Convert base64 image to a thumbnail (reduce size)
    img_data = b64decode(base_64_img_str)
    img = Image.open(io.BytesIO(img_data))
    img.thumbnail((200, 200))  # Adjust the size as needed for thumbnails

    # Add recommendation text overlay
    draw = ImageDraw.Draw(img)
    text = rec
    font = ImageFont.load_default()  # Adjust the font and size here

    # Calculate wrapped text dimensions
    max_text_width = img.width - 10  # Max width for wrapping text
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and draw.textlength(line + words[0], font=font)[0] <= max_text_width:
            line += words.pop(0) + ' '
        lines.append(line)
    wrapped_text = '\n'.join(lines)

    # Calculate text size after wrapping
    wrapped_text_width, wrapped_text_height = draw.textlength(wrapped_text, font=font)

    # Calculate box dimensions
    box_width = img.width
    box_height = wrapped_text_height + 10  # Adjust padding as needed

    # Draw black box dynamically sized for wrapped text
    draw.rectangle([(0, img.height - box_height), (img.width, img.height)], fill='black')

    # Calculate text position
    text_x = (img.width - wrapped_text_width) / 2
    text_y = img.height - box_height + (box_height - wrapped_text_height) / 2  # Center vertically

    # Draw wrapped text
    draw.text((text_x, text_y), wrapped_text, fill='white', font=font)

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    base_64_thumbnail_str = base64.b64encode(buffered.getvalue()).decode()

    return f"<td><img src='data:image/png;base64, {base_64_thumbnail_str}'></td>"


async def display_images(col1, products, bedrock_runtime):
    start_time_col1 = time.time()
    st.header("Images")

    # Assuming 'products' is a list of tuples (rec, attributes) required by generate_thumbnail
    image_elements = [generate_ai_thumbnail(product, attributes, bedrock_runtime) for product, attributes in products]

    # Wait for all thumbnails to be generated
    image_strips = await asyncio.gather(*image_elements)

    # Display the HTML table with all thumbnails
    st.markdown("".join(image_strips), unsafe_allow_html=True)

    end_time_col1 = time.time()
    st.write("Time to render Images:", end_time_col1 - start_time_col1)

    return image_strips

async def main(col1, products, bedrock_runtime):
    return await display_images(col1, products, bedrock_runtime)

# Run the main coroutine
if __name__ == "__main__":
    col1 = st.empty()  # Replace with actual Streamlit column
    products = [("Product description", "Product code"), ("Another product description", "Another product code")]  # Replace with actual products
    bedrock_runtime = None  # Replace with actual bedrock_runtime
    asyncio.run(main(col1, products, bedrock_runtime))