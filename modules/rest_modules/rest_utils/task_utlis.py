import asyncio
import logging
import traceback
from typing import Any

from fastapi import HTTPException

from modules.globals import session_store
from modules.rest_modules.rest_utils.resource_manager import ResourceManager
from modules.vector_index.vector_utils.chat_processor import process_chat_question_with_customer_attribute_identifier


async def process_chat_question(chat_request, session_id, resource_manager_param: ResourceManager) -> dict[str, Any] | dict[str, str | list[Any]]:
    try:
        (
            message,
            response_json,
            customer_attributes_retrieved,
            time_to_get_attributes,
        ) = await process_chat_question_with_customer_attribute_identifier(
            chat_request.question, chat_request.clear_history, session_id, resource_manager_param
        )

        if response_json is None:
            logging.error("fast_api_main/ Response json is None")
            raise HTTPException(status_code=500, detail="fast_api_main/ Error processing chat question, response is None")

        products = response_json.get("products", [])
        logging.info(f"fast_api_main/ Products retrieved: {products}")

        # Update the session history with the latest question and response
        session_store[session_id].append({"question": chat_request.question, "response": response_json})

        return {
            "message": message,
            "customer_attributes_retrieved": customer_attributes_retrieved,
            "time_to_get_attributes": time_to_get_attributes,
            "products": products,
        }
    except asyncio.CancelledError:
        logging.info(f"fast_api_main/ Task for session_id {session_id} was cancelled due to new question.")
        return {"message": "Task cancelled due to new question", "products": []}
    except Exception as e:
        logging.error(f"Error in fast_api_main/process_chat_question: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
