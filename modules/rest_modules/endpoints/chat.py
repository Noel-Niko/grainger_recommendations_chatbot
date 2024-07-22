import asyncio
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, Request
from modules.rest_modules.models import ChatRequest
from modules.rest_modules.rest_utils.task_utlis import process_chat_question
from modules.globals import session_store, current_tasks
from modules.utils import get_resource_manager
from modules.rest_modules.rest_utils.resource_manager import ResourceManager

router = APIRouter()

@router.post("/ask_question")
async def ask_question(
    chat_request: ChatRequest,
    request: Request,
    resource_manager_param: ResourceManager = Depends(get_resource_manager)
):
    try:
        session_id = request.headers.get("session-id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")

        if session_id not in session_store:
            session_store[session_id] = []
            logging.info(f"Adding new session ID {session_id} to session_store")

        logging.info(f"Received question: {chat_request.question} with session_id: {session_id}")

        if session_id in current_tasks and not current_tasks[session_id].done():
            logging.info(f"Cancelling task for session ID: {session_id} due to new question.")
            current_tasks[session_id].cancel()
            await current_tasks[session_id]

        task = asyncio.create_task(process_chat_question(chat_request, session_id, resource_manager_param))
        current_tasks[session_id] = task

        response = await task

        return response

    except Exception as e:
        logging.error(f"Error in ask_question: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")
