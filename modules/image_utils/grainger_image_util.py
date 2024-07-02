# file: image_utils.py

import asyncio
import logging

import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from IPython.core.display import HTML
import pandas as pd
import time


async def generate_grainger_thumbnail(image_url, code, name):
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            img_data = await resp.read()

    img = Image.open(io.BytesIO(img_data))
    img.thumbnail((200, 200))  # Adjust the size as needed for thumbnails

    draw = ImageDraw.Draw(img)
    text = f"{code}: {name}"
    font = ImageFont.load_default()  # Adjust the font and size here

    max_text_width = img.width - 10  # Max width for wrapping text
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and draw.textsize(line + words[0], font=font)[0] <= max_text_width:
            line += words.pop(0) + ' '
        lines.append(line)
    wrapped_text = '\n'.join(lines)

    wrapped_text_width, wrapped_text_height = draw.textsize(wrapped_text, font=font)

    box_width = img.width
    box_height = wrapped_text_height + 10  # Adjust padding as needed

    draw.rectangle([(0, img.height - box_height), (img.width, img.height)], fill='black')

    text_x = (img.width - wrapped_text_width) / 2
    text_y = img.height - box_height + (box_height - wrapped_text_height) / 2  # Center vertically

    draw.text((text_x, text_y), wrapped_text, fill='white', font=font)

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    base_64_thumbnail_str = base64.b64encode(buffered.getvalue()).decode()

    return f"<td><img src='data:image/jpeg;base64,{base_64_thumbnail_str}'></td>"


async def main(image_url_maps, df):
    start_time = time.time()
    logging.info("Generating thumbnails for Grainger products...")
    logging.info(f"Image URL Maps: {image_url_maps}")
    image_strips = [
        await generate_grainger_thumbnail(item["Image URL"], item["Code"], df.loc[df['Code'] == item["Code"], 'Name'].iloc[0])
        for item in image_url_maps if item
    ]

    html_content = "<table><tr>" + "".join(image_strips) + "</tr></table>"

    total_time = time.time() - start_time
    print("Total Image Time:", total_time)

    return html_content, total_time
