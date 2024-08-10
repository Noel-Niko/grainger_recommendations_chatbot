import asyncio

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Depends, FastAPI, HTTPException, Request
from modules.rest_modules.models import ChatRequest
from modules.rest_modules.rest_utils.resource_manager import ResourceManager
# from modules.vector_index.vector_utils.chat_processor import process_chat_question_with_customer_attribute_identifier
from modules.globals import current_tasks, session_store

# Import the FastAPI app and router
from fastapi import APIRouter

# Assuming you have a FastAPI app setup somewhere
app = FastAPI()

# Import the router
from modules.rest_modules.endpoints.chat import process_chat_question, process_question_task, router

# Add the router to the FastAPI app
app.include_router(router)


# Fixture for the FastAPI test client
# @pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_ask_question_without_session_id(client):
    chat_request = {
        "question": "What is the meaning of life?",
        "clear_history": False
    }

    response = client.post("/ask_question", json=chat_request)
    assert response.status_code == 400
    assert response.json() == {"detail": "Session ID is required"}


@pytest.mark.asyncio
async def test_ask_question_new_session(client):
    chat_request = {
        "question": "What is the meaning of life?",
        "clear_history": False
    }
    session_id = "test-session-id"

    with patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock) as mock_task:
        mock_task.return_value = {"message": "42", "products": []}

        headers = {"session-id": session_id}
        response = client.post("/ask_question", json=chat_request, headers=headers)

        assert response.status_code == 200
        assert response.json() == {"message": "42", "products": []}
        assert session_id in session_store
        assert session_id in current_tasks


@pytest.mark.asyncio
async def test_ask_question_with_existing_task(client):
    chat_request = {
        "question": "What is the meaning of life?",
        "clear_history": False
    }
    session_id = "test-session-id"

    current_tasks[session_id] = AsyncMock()
    current_tasks[session_id].done.return_value = False

    with patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock) as mock_task:
        mock_task.return_value = {"message": "42", "products": []}

        headers = {"session-id": session_id}
        response = client.post("/ask_question", json=chat_request, headers=headers)

        assert response.status_code == 200
        assert response.json() == {"message": "42", "products": []}
        assert session_id in session_store
        assert session_id in current_tasks
        current_tasks[session_id].cancel.assert_called_once()
        await current_tasks[session_id]


@pytest.mark.asyncio
async def test_process_question_task_success():
    chat_request = ChatRequest(question="What is the meaning of life?", clear_history=False)
    session_id = "test-session-id"

    with patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
               return_value=("42", {"products": []}, None, None)):
        response = await process_question_task(chat_request, session_id, ResourceManager())

        assert response["message"] == "42"
        assert response["products"] == []
        assert session_id in session_store
        assert len(session_store[session_id]) == 1


@pytest.mark.asyncio
async def test_process_question_task_cancelled():
    chat_request = ChatRequest(question="What is the meaning of life?", clear_history=False)
    session_id = "test-session-id"

    with patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
               side_effect=asyncio.CancelledError):
        response = await process_question_task(chat_request, session_id, ResourceManager())

        assert response["message"] == "Task cancelled due to new question"
        assert response["products"] == []


# @pytest.mark.asyncio
async def test_process_chat_question_success():
    session_id = "test-session-id"
    session_store[session_id] = []

    with patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
               return_value=("42", {"products": []}, None, None)):
        message, response_json, customer_attributes_retrieved, time_to_get_attributes =  process_chat_question(
            "What is the meaning of life?", False, session_id, ResourceManager()
        )

        assert message == "42"
        assert response_json == {"products": []}
        assert session_id in session_store
        assert len(session_store[session_id]) == 1

# import asyncio
# import unittest
# from unittest.mock import AsyncMock, MagicMock, patch
#
# import pytest
# from fastapi import FastAPI, HTTPException
# from fastapi.testclient import TestClient
# from starlette.middleware.sessions import SessionMiddleware
# from modules.rest_modules.endpoints.chat import process_chat_question, process_question_task, router
# from modules.rest_modules.models import ChatRequest
# from modules.rest_modules.rest_utils.resource_manager import ResourceManager
#
# app = FastAPI()
# app.add_middleware(SessionMiddleware, secret_key="some-secret")
# app.include_router(router)
#
#
# class TestFastApiMain(unittest.TestCase):
#     def setUp(self):
#         self.client = TestClient(app)
#         self.session_id = "test-session-id"
#         self.headers = {"session-id": self.session_id}
#         self.chat_request = ChatRequest(question="What products do you have?", clear_history=False)
#
#     @patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
#            new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.get_resource_manager", new_callable=AsyncMock)
#     def test_ask_question_success(self, mock_get_resource_manager, mock_process_question_task,
#                                   mock_process_chat_question):
#         # Your test logic here, using the client to send requests
#
#         response = self.client.post("/ask_question", json=self.chat_request.dict(), headers=self.headers)
#
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json(), mock_process_question_task.return_value)
#
#     # def setUp(self):
#     #     self.client = TestClient(app)
#     #     self.session_id = "test-session-id"
#     #     self.headers = {"session-id": self.session_id}
#     #     self.chat_request = ChatRequest(question="What products do you have?", clear_history=False)
#
#     @patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
#            new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.get_resource_manager", new_callable=AsyncMock)
#     def test_ask_question_success(self, mock_get_resource_manager, mock_process_question_task,
#                                   mock_process_chat_question):
#         mock_get_resource_manager.return_value = ResourceManager()
#         mock_process_question_task.return_value = {
#             "message": "Here are some products",
#             "customer_attributes_retrieved": "{}",
#             "time_to_get_attributes": 1,
#             "products": [{"product": "example", "code": "123"}]
#         }
#
#         response = self.client.post("/ask_question", json=self.chat_request.dict(), headers=self.headers)
#
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.json(), mock_process_question_task.return_value)
#
#     @patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
#            new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.get_resource_manager", new_callable=AsyncMock)
#     def test_ask_question_no_session_id(self, mock_get_resource_manager, mock_process_question_task,
#                                         mock_process_chat_question):
#         response = self.client.post("/ask_question", json=self.chat_request.dict())
#
#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.json(), {"detail": "Session ID is required"})
#
#     @patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
#            new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock)
#     @patch("modules.rest_modules.endpoints.chat.get_resource_manager", new_callable=AsyncMock)
#     def test_ask_question_internal_server_error(self, mock_get_resource_manager, mock_process_question_task,
#                                                 mock_process_chat_question):
#         mock_process_question_task.side_effect = HTTPException(500, "Internal Server Error")
#         response = self.client.post("/ask_question", json=self.chat_request.dict(), headers=self.headers)
#
#         self.assertEqual(response.status_code, 500)
#         self.assertEqual(response.json(), {"detail": "Internal Server Error"})
#
#     # @patch("modules.rest_modules.endpoints.chat.process_chat_question", new_callable=AsyncMock)
#     # def test_process_question_task_success(self, mock_process_chat_question):
#     #     mock_process_chat_question.return_value = (
#     #     "message", {"products": [{"product": "example", "code": "123"}]}, "{}", 1)
#     #     resource_manager = ResourceManager()
#     #
#     #     response = asyncio.run(process_question_task(self.chat_request, self.session_id, resource_manager))
#     #
#     #     self.assertEqual(response["message"], "message")
#     #     self.assertEqual(response["products"], [{"product": "example", "code": "123"}])
#
#     @patch("modules.rest_modules.endpoints.chat.process_chat_question", new_callable=AsyncMock)
#     def test_process_question_task_cancelled_error(self, mock_process_chat_question):
#         mock_process_chat_question.side_effect = asyncio.CancelledError()
#         resource_manager = ResourceManager()
#
#         response = asyncio.run(process_question_task(self.chat_request, self.session_id, resource_manager))
#
#         self.assertEqual(response["message"], "Task cancelled due to new question")
#         self.assertEqual(response["products"], [])
#
#     @patch("modules.rest_modules.endpoints.chat.process_chat_question", new_callable=AsyncMock)
#     def test_process_question_task_internal_server_error(self, mock_process_chat_question):
#         mock_process_chat_question.side_effect = Exception("Some error")
#         resource_manager = ResourceManager()
#
#         with self.assertRaises(HTTPException) as context:
#             asyncio.run(process_question_task(self.chat_request, self.session_id, resource_manager))
#
#         self.assertEqual(context.exception.status_code, 500)
#         self.assertEqual(context.exception.detail, "Internal Server Error")
#
#     @patch("modules.vector_index.vector_utils.chat_processor")
#     def test_process_chat_question_success(self, mock_chat_processor):
#         mock_chat_processor = MagicMock()
#         mock_chat_processor.process_chat_question_with_customer_attribute_identifier.return_value = (
#             "message", {"products": [{"product": "example", "code": "123"}]}, "{}", 1
#         )
#
#         resource_manager = ResourceManager()
#
#         response = asyncio.run(
#             process_chat_question(self.chat_request.question, False, self.session_id, resource_manager))
#
#         self.assertEqual(response[0], "message")
#         self.assertEqual(response[1], {"products": [{"product": "example", "code": "123"}]})
#
#     # @patch("modules.vector_index.vector_utils.chat_processor.process_chat_question_with_customer_attribute_identifier", new_callable=AsyncMock)
#     # def test_process_chat_question_internal_server_error(self, mock_process_chat_question_with_customer_attribute_identifier):
#     #     mock_process_chat_question_with_customer_attribute_identifier.side_effect = Exception("Some error")
#     #     resource_manager = ResourceManager()
#     #
#     #     with self.assertRaises(Exception) as context:
#     #         asyncio.run(process_chat_question(self.chat_request.question, False, self.session_id, resource_manager))
#     #
#     #     self.assertEqual(str(context.exception), "Some error")
#
#
# if __name__ == "__main__":
#     unittest.main()
