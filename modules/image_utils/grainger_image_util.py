import logging
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import pandas as pd
import time
import asyncio

tag = 'grainger_image_util'

async def get_images(recommendations_list, df):
    image_tasks = []
    image_data = []
    total_image_time = 0.0

    async with aiohttp.ClientSession() as session:
        checked = []
        for item in recommendations_list:
            parts = item.split(', ')
            code = parts[-1]
            logging.info(f"{tag} item.part[-1]: {parts[-1]} item.part[0]: {parts[0]}")
            if code in df['Code'].values:
                if code not in checked:
                    start_time = time.time()
                    image_url = df.loc[df['Code'] == code, 'PictureUrl600'].iloc[0]
                    end_time = time.time()
                    total_image_time += end_time - start_time
                    print(f"Fetched image URL {image_url} for {code} in {end_time - start_time:.2f} seconds")

                    # Add image fetching task
                    image_tasks.append(fetch_image(session, code, image_url))
                    checked.append(code)
            else:
                print(f"Code {code} not found in the dataframe.")

        # Gather all image tasks concurrently
        image_results = await asyncio.gather(*image_tasks)
    return image_results, total_image_time


async def fetch_image(session, code, image_url):
    async with session.get(image_url) as response:
        if response.status == 200:
            img_data = await response.read()  # Read the image data
            return {"Code": code, "Image Data": img_data}
        else:
            return f"Failed to fetch image for {code}: {image_url}"


async def generate_single_grainger_thumbnail(image_data):
    img = Image.open(io.BytesIO(image_data))
    img.thumbnail((200, 200))

    draw = ImageDraw.Draw(img)
    text = f"{image_data['Code']}: {image_data['Code']} Name Placeholder"  # Adjust based on actual data structure
    font = ImageFont.load_default()

    max_text_width = img.width - 10
    lines = []
    words = text.split()
    current_line = ''
    while words:
        word = words.pop(0)
        if draw.textlength(current_line + word, font=font) > max_text_width:
            lines.append(current_line.strip())
            current_line = word + ' '
        else:
            current_line += word + ' '

    if current_line.strip():
        lines.append(current_line.strip())

    wrapped_text = '\n'.join(lines)

    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    box_width = img.width
    box_height = text_height + 10

    draw.rectangle([(0, img.height - box_height), (img.width, img.height)], fill='black')

    text_x = (img.width - text_width) / 2
    text_y = img.height - box_height + (box_height - text_height) / 2

    draw.text((text_x, text_y), wrapped_text, fill='white', font=font)

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    base_64_thumbnail_str = base64.b64encode(buffered.getvalue()).decode()

    return f"<td><img src='data:image/jpeg;base64,{base_64_thumbnail_str}'></td>"


# Example usage
# recommendations_list = [...]  # Your list of recommendations
# df = pd.DataFrame(...)  # Your DataFrame with product information
# image_data, total_time = await get_images(recommendations_list, df)
# for data in image_data:
#     result = await generate_single_grainger_thumbnail(data["Image Data"])
#     print(result)


# import asyncio
# import logging
# import aiohttp
# from PIL import Image, ImageDraw, ImageFont
# import io
# import base64
# import pandas as pd
# import time
# import asyncio
# from PIL import Image, ImageDraw, ImageFont
# import io
# import aiohttp
# import base64
#
# async def get_images(recommendations_list, df):
#     image_tasks = []
#     image_urls = []
#     total_image_time = 0.0
#
#     async with aiohttp.ClientSession() as session:
#         for item in recommendations_list:
#             # Split the recommendation string to get text and code
#             parts = item.split(', ')
#             code = parts[-1]  # Code is the last element
#
#             if code in df['Code'].values:
#                 start_time = time.time()
#                 image_url = df.loc[df['Code'] == code, 'PictureUrl600'].iloc[0]
#                 end_time = time.time()
#                 total_image_time += end_time - start_time
#                 image_urls.append({"Code": code, "Image URL": image_url})
#                 print(f"Fetched image URL for {code} in {end_time - start_time:.2f} seconds")
#
#                 # Add image fetching task
#                 image_tasks.append(fetch_image(session, code, image_url))
#             else:
#                 print(f"Code {code} not found in the dataframe.")
#
#         # Gather all image tasks concurrently
#         image_results = await asyncio.gather(*image_tasks)
#         logging.info(f"image_results: {image_results}")
#     # return image_results, total_image_time
#     return image_urls, total_image_time
#
# async def fetch_image(session, code, image_url):
#     async with session.get(image_url) as response:
#         if response.status == 200:
#             await response.read()  # Simulate fetching image (you can save or process the image here)
#             return f"Image URL for {code}: {image_url}"
#         else:
#             return f"Failed to fetch image for {code}: {image_url}"
#
# async def generate_single_grainger_thumbnail(image_url, code, name):
#     async with aiohttp.ClientSession() as session:
#         async with session.get(image_url) as resp:
#             img_data = await resp.read()
#
#     img = Image.open(io.BytesIO(img_data))
#     img.thumbnail((200, 200))  # Adjust the size as needed for thumbnails
#
#     draw = ImageDraw.Draw(img)
#     text = f"{code}: {name}"
#     font = ImageFont.load_default()  # Adjust the font and size here
#
#     max_text_width = img.width - 10  # Max width for wrapping text
#     lines = []
#     words = text.split()
#     current_line = ''
#     while words:
#         word = words.pop(0)
#         if draw.textlength(current_line + word, font=font) > max_text_width:
#             lines.append(current_line.strip())
#             current_line = word + ' '
#         else:
#             current_line += word + ' '
#
#     if current_line.strip():
#         lines.append(current_line.strip())
#
#     wrapped_text = '\n'.join(lines)
#
#     # Assuming the rest of your function remains unchanged up to this point
#
#     # Calculate text width and height using textbox
#     bbox = draw.textbbox((0, 0), wrapped_text, font=font)
#     text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
#
#     box_width = img.width
#     box_height = text_height + 10  # Adjust padding as needed
#
#     draw.rectangle([(0, img.height - box_height), (img.width, img.height)], fill='black')
#
#     text_x = (img.width - text_width) / 2
#     text_y = img.height - box_height + (box_height - text_height) / 2  # Center vertically
#
#     draw.text((text_x, text_y), wrapped_text, fill='white', font=font)
#
#     buffered = io.BytesIO()
#     img.save(buffered, format="JPEG")
#     base_64_thumbnail_str = base64.b64encode(buffered.getvalue()).decode()
#
#     return f"<td><img src='data:image/jpeg;base64,{base_64_thumbnail_str}'></td>"


# async def generate_single_grainger_thumbnail(image_url, code, name):
#     async with aiohttp.ClientSession() as session:
#         async with session.get(image_url) as resp:
#             img_data = await resp.read()
#
#     img = Image.open(io.BytesIO(img_data))
#     img.thumbnail((200, 200))  # Adjust the size as needed for thumbnails
#
#     draw = ImageDraw.Draw(img)
#     text = f"{code}: {name}"
#     font = ImageFont.load_default()  # Adjust the font and size here
#
#     max_text_width = img.width - 10  # Max width for wrapping text
#     lines = []
#     words = text.split()
#     while words:
#         line = ''
#         while words and draw.textlength(line + words[0], font=font) <= max_text_width:
#             line += words.pop(0) + ' '
#         lines.append(line)
#     wrapped_text = '\n'.join(lines)
#
#     wrapped_text_width, wrapped_text_height = draw.textlength(wrapped_text, font=font)
#
#     box_width = img.width
#     box_height = wrapped_text_height + 10  # Adjust padding as needed
#
#     draw.rectangle([(0, img.height - box_height), (img.width, img.height)], fill='black')
#
#     text_x = (img.width - wrapped_text_width) / 2
#     text_y = img.height - box_height + (box_height - wrapped_text_height) / 2  # Center vertically
#
#     draw.text((text_x, text_y), wrapped_text, fill='white', font=font)
#
#     buffered = io.BytesIO()
#     img.save(buffered, format="JPEG")
#     base_64_thumbnail_str = base64.b64encode(buffered.getvalue()).decode()
#
#     return f"<td><img src='data:image/jpeg;base64,{base_64_thumbnail_str}'></td>"

async def generate_grainger_thumbnails(image_urls, df):
    start_time = time.time()
    logging.info("Generating thumbnails for Grainger products...")
    logging.info(f"Image URL Maps: {image_urls}")

    image_strips = [
        await generate_single_grainger_thumbnail(item["Image URL"], item["Code"],
                                                 df.loc[df['Code'] == item["Code"], 'Name'].iloc[0])
        for item in image_urls if item
    ]

    html_content = "<table><tr>" + "".join(image_strips) + "</tr></table>"

    total_time = time.time() - start_time
    print("Total Image Time:", total_time)

    return html_content, total_time


async def main(image_urls, df):
    return await generate_grainger_thumbnails(image_urls, df)

# import asyncio
# import logging
# import aiohttp
# from PIL import Image, ImageDraw, ImageFont
# import io
# import base64
# import pandas as pd
# import time
#
# async def get_images(recommendations_list, df):
#     image_tasks = []
#     image_urls = []
#     total_image_time = 0.0
#
#     async with aiohttp.ClientSession() as session:
#         for item in recommendations_list:
#             # Split the recommendation string to get text and code
#             parts = item.split(', ')
#             code = parts[-1]  # Code is the last element
#
#             if code in df['Code'].values:
#                 start_time = time.time()
#                 image_url = df.loc[df['Code'] == code, 'PictureUrl600'].iloc[0]
#                 end_time = time.time()
#                 total_image_time += end_time - start_time
#                 image_urls.append({"Code": code, "Image URL": image_url})
#                 print(f"Fetched image URL for {code} in {end_time - start_time:.2f} seconds")
#
#                 # Add image fetching task
#                 image_tasks.append(fetch_image(session, code, image_url))
#             else:
#                 print(f"Code {code} not found in the dataframe.")
#
#         # Gather all image tasks concurrently
#         image_results = await asyncio.gather(*image_tasks)
#
#     return image_results, total_image_time
#
# async def fetch_image(session, code, image_url):
#     async with session.get(image_url) as response:
#         if response.status == 200:
#             await response.read()  # Simulate fetching image (you can save or process the image here)
#             return f"Image URL for {code}: {image_url}"
#         else:
#             return f"Failed to fetch image for {code}: {image_url}"
#
# async def generate_single_grainger_thumbnail(image_url, code, name):
#     async with aiohttp.ClientSession() as session:
#         async with session.get(image_url) as resp:
#             img_data = await resp.read()
#
#     img = Image.open(io.BytesIO(img_data))
#     img.thumbnail((200, 200))  # Adjust the size as needed for thumbnails
#
#     draw = ImageDraw.Draw(img)
#     text = f"{code}: {name}"
#     font = ImageFont.load_default()  # Adjust the font and size here
#
#     max_text_width = img.width - 10  # Max width for wrapping text
#     lines = []
#     words = text.split()
#     while words:
#         line = ''
#         while words and draw.textsize(line + words[0], font=font)[0] <= max_text_width:
#             line += words.pop(0) + ' '
#         lines.append(line)
#     wrapped_text = '\n'.join(lines)
#
#     wrapped_text_width, wrapped_text_height = draw.textsize(wrapped_text, font=font)
#
#     box_width = img.width
#     box_height = wrapped_text_height + 10  # Adjust padding as needed
#
#     draw.rectangle([(0, img.height - box_height), (img.width, img.height)], fill='black')
#
#     text_x = (img.width - wrapped_text_width) / 2
#     text_y = img.height - box_height + (box_height - wrapped_text_height) / 2  # Center vertically
#
#     draw.text((text_x, text_y), wrapped_text, fill='white', font=font)
#
#     buffered = io.BytesIO()
#     img.save(buffered, format="JPEG")
#     base_64_thumbnail_str = base64.b64encode(buffered.getvalue()).decode()
#
#     return f"<td><img src='data:image/jpeg;base64,{base_64_thumbnail_str}'></td>"
#
# async def generate_grainger_thumbnails(image_urls, df):
#     start_time = time.time()
#     logging.info("Generating thumbnails for Grainger products...")
#     logging.info(f"Image URL Maps: {image_urls}")
#
#     image_strips = [
#         await generate_single_grainger_thumbnail(item["Image URL"], item["Code"], df.loc[df['Code'] == item["Code"], 'Name'].iloc[0])
#         for item in image_urls if item
#     ]
#
#     html_content = "<table><tr>" + "".join(image_strips) + "</tr></table>"
#
#     total_time = time.time() - start_time
#     print("Total Image Time:", total_time)
#
#     return html_content, total_time
#
# async def main(image_urls, df):
#     # This function can be used for further integration or standalone execution
#     return await generate_grainger_thumbnails(image_urls, df)
#
#
# # # file: image_utils.py
# #
# # import asyncio
# # import logging
# #
# # import aiohttp
# # from PIL import Image, ImageDraw, ImageFont
# # import io
# # import base64
# # from IPython.core.display import HTML
# # import pandas as pd
# # import time
# #
# #
# # async def get_images(recommendations_list, df):
# #     image_tasks = []
# #     image_urls = []
# #     total_image_time = 0.0
# #
# #     async with aiohttp.ClientSession() as session:
# #         for item in recommendations_list:
# #             # Split the recommendation string to get text and code
# #             parts = item.split(', ')
# #             code = parts[-1]  # Code is the last element
# #             text = ', '.join(parts[:-1])  # Text is everything except the code
# #
# #             if code in df['Code'].values:
# #                 start_time = time.time()
# #                 image_url = df.loc[df['Code'] == code, 'PictureUrl600'].iloc[0]
# #                 end_time = time.time()
# #                 total_image_time += end_time - start_time
# #                 image_urls.append({"Code": code, "Image URL": image_url})
# #                 print(f"Fetched image URL for {code} in {end_time - start_time:.2f} seconds")
# #
# #                 # Add image fetching task
# #                 image_tasks.append(fetch_image(session, code, image_url))
# #             else:
# #                 print(f"Code {code} not found in the dataframe.")
# #
# #         # Gather all image tasks concurrently
# #         image_results = await asyncio.gather(*image_tasks)
# #
# #     return image_results, total_image_time
# #
# #
# # async def fetch_image(session, code, image_url):
# #     async with session.get(image_url) as response:
# #         if response.status == 200:
# #             await response.read()  # Simulate fetching image (you can save or process the image here)
# #             return f"Image URL for {code}: {image_url}"
# #         else:
# #             return f"Failed to fetch image for {code}: {image_url}"
# #
# #
# #
# # async def generate_single_grainger_thumbnail(image_url, code, name):
# #     async with aiohttp.ClientSession() as session:
# #         async with session.get(image_url) as resp:
# #             img_data = await resp.read()
# #
# #     img = Image.open(io.BytesIO(img_data))
# #     img.thumbnail((200, 200))  # Adjust the size as needed for thumbnails
# #
# #     draw = ImageDraw.Draw(img)
# #     text = f"{code}: {name}"
# #     font = ImageFont.load_default()  # Adjust the font and size here
# #
# #     max_text_width = img.width - 10  # Max width for wrapping text
# #     lines = []
# #     words = text.split()
# #     while words:
# #         line = ''
# #         while words and draw.textsize(line + words[0], font=font)[0] <= max_text_width:
# #             line += words.pop(0) + ' '
# #         lines.append(line)
# #     wrapped_text = '\n'.join(lines)
# #
# #     wrapped_text_width, wrapped_text_height = draw.textsize(wrapped_text, font=font)
# #
# #     box_width = img.width
# #     box_height = wrapped_text_height + 10  # Adjust padding as needed
# #
# #     draw.rectangle([(0, img.height - box_height), (img.width, img.height)], fill='black')
# #
# #     text_x = (img.width - wrapped_text_width) / 2
# #     text_y = img.height - box_height + (box_height - wrapped_text_height) / 2  # Center vertically
# #
# #     draw.text((text_x, text_y), wrapped_text, fill='white', font=font)
# #
# #     buffered = io.BytesIO()
# #     img.save(buffered, format="JPEG")
# #     base_64_thumbnail_str = base64.b64encode(buffered.getvalue()).decode()
# #
# #     return f"<td><img src='data:image/jpeg;base64,{base_64_thumbnail_str}'></td>"
# #
# # async def generate_grainger_thumbnails(image_url_maps, df):
# #     start_time = time.time()
# #     logging.info("Generating thumbnails for Grainger products...")
# #     logging.info(f"Image URL Maps: {image_url_maps}")
# #     image_strips = [
# #         await generate_single_grainger_thumbnail(item["Image URL"], item["Code"], df.loc[df['Code'] == item["Code"], 'Name'].iloc[0])
# #         for item in image_url_maps if item
# #     ]
# #
# #     html_content = "<table><tr>" + "".join(image_strips) + "</tr></table>"
# #
# #     total_time = time.time() - start_time
# #     print("Total Image Time:", total_time)
# #
# #     return html_content, total_time
# #
# # async def main(image_url_maps, df):
# #     start_time = time.time()
# #     logging.info("Generating thumbnails for Grainger products...")
# #     logging.info(f"Image URL Maps: {image_url_maps}")
# #     image_strips = [
# #         await generate_single_grainger_thumbnail(item["Image URL"], item["Code"],
# #                                                  df.loc[df['Code'] == item["Code"], 'Name'].iloc[0])
# #         for item in image_url_maps if item
# #     ]
# #
# #     html_content = "<table><tr>" + "".join(image_strips) + "</tr></table>"
# #
# #     total_time = time.time() - start_time
# #     print("Total Image Time:", total_time)
# #
# #     return html_content, total_time
