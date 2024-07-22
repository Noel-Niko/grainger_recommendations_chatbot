import asyncio
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, Request
from modules.rest_modules.models import ChatRequest
from modules.rest_modules.rest_utils.resource_manager import ResourceManager
from modules.vector_index.vector_utils.chat_processor import process_chat_question_with_customer_attribute_identifier
from modules.globals import session_store, current_tasks

router = APIRouter()
tag = "fast_api_main"

async def get_resource_manager():
    from modules.fast_api_main import resource_manager
    return resource_manager

resource_manager_dependency = Depends(get_resource_manager)

@router.post("/ask_question")
async def ask_question(
    chat_request: ChatRequest,
    request: Request,
    resource_manager_param: ResourceManager = resource_manager_dependency
):
    try:
        session_id = request.headers.get("session-id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")

        if session_id not in session_store:
            session_store[session_id] = []
            logging.info(f"{tag}/ Adding new session ID {session_id} to session_store")

        logging.info(f"{tag}/ Received question: {chat_request.question} with session_id: {session_id}")

        if session_id in current_tasks and not current_tasks[session_id].done():
            logging.info(f"Cancelling task for session ID: {session_id} due to new question.")
            current_tasks[session_id].cancel()
            await current_tasks[session_id]

        task = asyncio.create_task(process_question_task(chat_request, session_id, resource_manager_param))
        current_tasks[session_id] = task

        response = await task

        return response

    except Exception as e:
        logging.error(f"Error in {tag}/ask_question: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def process_question_task(chat_request, session_id, resource_manager_param):
    try:
        message, response_json, customer_attributes_retrieved, time_to_get_attributes = await process_chat_question(
            chat_request.question, chat_request.clear_history, session_id, resource_manager_param
        )

        if response_json is None:
            logging.error(f"{tag}/ Response json is None")
            raise HTTPException(status_code=500, detail=f"{tag}/ Error processing chat question, response is None")

        products = response_json.get('products', [])
        logging.info(f"{tag}/ Products retrieved: {products}")

        session_store[session_id].append({
            "question": chat_request.question,
            "response": response_json
        })

        return {
            "message": message,
            "customer_attributes_retrieved": customer_attributes_retrieved,
            "time_to_get_attributes": time_to_get_attributes,
            "products": products
        }
    except asyncio.CancelledError:
        logging.info(f"{tag}/ Task for session_id {session_id} was cancelled due to new question.")
        return {
            "message": "Task cancelled due to new question",
            "products": []
        }
    except Exception as e:
        logging.error(f"Error in {tag}/process_question_task: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def process_chat_question(question, clear_history, session_id, resource_manager_param):
    try:
        if clear_history:
            logging.info(f"{tag}/ Clearing chat history for session_id: {session_id}")
            session_store[session_id] = []

        chat_history = session_store.get(session_id, [])
        logging.info(f"{tag}/ Current chat history for session_id {session_id}: {chat_history}")

        logging.info(f"{tag}/ Processing question: {question}")
        message, response_json, customer_attributes_retrieved, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
            question,
            resource_manager_param.vectorstore_faiss_doc,
            resource_manager_param.llm,
            chat_history
        )

        chat_history.append(
            f"QUESTION: {question}. MESSAGE: {message}. CUSTOMER ATTRIBUTES: {customer_attributes_retrieved}")
        session_store[session_id] = chat_history

        return message, response_json, customer_attributes_retrieved, time_to_get_attributes
    except Exception as e:
        logging.error(f"{tag}/ Error processing chat question: {str(e)}")
        logging.error(traceback.format_exc())
        raise
