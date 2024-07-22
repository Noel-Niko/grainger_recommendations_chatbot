import base64
import io
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, Request
from PIL import Image
from modules.rest_modules.rest_utils.resource_manager import ResourceManager
from modules.rest_modules.rest_utils.image_utils.grainger_image_util import get_images
from modules.globals import session_store, current_tasks
from modules.utils import get_resource_manager

router = APIRouter()

@router.post("/fetch_images")
async def fetch_images(
    request: Request,
    resource_manager_param: ResourceManager = Depends(get_resource_manager)
):
    try:
        products = await request.json()
        recommendations_list = [f"{product['product']}, {product['code']}" for product in products]
        logging.info(f"Fetching images for products: {recommendations_list}")
        image_data, total_image_time = await get_images(recommendations_list, resource_manager_param.df)
        logging.info(f"Total time to fetch images: {total_image_time} seconds.\nImage data: {image_data}")

        image_responses = []
        for image_info in image_data:
            try:
                img = Image.open(io.BytesIO(image_info["Image Data"]))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                encoded_image = base64.b64encode(img_byte_arr).decode('utf-8')
                image_responses.append({
                    "code": image_info["Code"],
                    "image_data": encoded_image
                })
            except Exception as e:
                logging.error(f"Error processing image: {e}")
        return image_responses
    except Exception as e:
        logging.error(f"Error fetching images: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error fetching images")
