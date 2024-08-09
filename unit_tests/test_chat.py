import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from modules.rest_modules.endpoints.chat import process_chat_question, process_question_task, router
from modules.rest_modules.models import ChatRequest
from modules.rest_modules.rest_utils.resource_manager import ResourceManager

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="some-secret")
app.include_router(router)


class TestFastApiMain(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.session_id = "test-session-id"
        self.headers = {"session-id": self.session_id}
        self.chat_request = ChatRequest(question="What products do you have?", clear_history=False)

    @patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
           new_callable=AsyncMock)
    @patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock)
    @patch("modules.rest_modules.endpoints.chat.get_resource_manager", new_callable=AsyncMock)
    def test_ask_question_success(self, mock_get_resource_manager, mock_process_question_task,
                                  mock_process_chat_question):
        mock_get_resource_manager.return_value = ResourceManager()
        mock_process_question_task.return_value = {
            "message": "Here are some products",
            "customer_attributes_retrieved": "{}",
            "time_to_get_attributes": 1,
            "products": [{"product": "example", "code": "123"}]
        }

        response = self.client.post("/ask_question", json=self.chat_request.dict(), headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_process_question_task.return_value)

    @patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
           new_callable=AsyncMock)
    @patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock)
    @patch("modules.rest_modules.endpoints.chat.get_resource_manager", new_callable=AsyncMock)
    def test_ask_question_no_session_id(self, mock_get_resource_manager, mock_process_question_task,
                                        mock_process_chat_question):
        response = self.client.post("/ask_question", json=self.chat_request.dict())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Session ID is required"})

    @patch("modules.rest_modules.endpoints.chat.process_chat_question_with_customer_attribute_identifier",
           new_callable=AsyncMock)
    @patch("modules.rest_modules.endpoints.chat.process_question_task", new_callable=AsyncMock)
    @patch("modules.rest_modules.endpoints.chat.get_resource_manager", new_callable=AsyncMock)
    def test_ask_question_internal_server_error(self, mock_get_resource_manager, mock_process_question_task,
                                                mock_process_chat_question):
        mock_process_question_task.side_effect = HTTPException(500, "Internal Server Error")
        response = self.client.post("/ask_question", json=self.chat_request.dict(), headers=self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Internal Server Error"})

    @patch("modules.rest_modules.endpoints.chat.process_chat_question", new_callable=AsyncMock)
    def test_process_question_task_success(self, mock_process_chat_question):
        mock_process_chat_question.return_value = (
        "message", {"products": [{"product": "example", "code": "123"}]}, "{}", 1)
        resource_manager = ResourceManager()

        response = asyncio.run(process_question_task(self.chat_request, self.session_id, resource_manager))

        self.assertEqual(response["message"], "message")
        self.assertEqual(response["products"], [{"product": "example", "code": "123"}])

    @patch("modules.rest_modules.endpoints.chat.process_chat_question", new_callable=AsyncMock)
    def test_process_question_task_cancelled_error(self, mock_process_chat_question):
        mock_process_chat_question.side_effect = asyncio.CancelledError()
        resource_manager = ResourceManager()

        response = asyncio.run(process_question_task(self.chat_request, self.session_id, resource_manager))

        self.assertEqual(response["message"], "Task cancelled due to new question")
        self.assertEqual(response["products"], [])

    @patch("modules.rest_modules.endpoints.chat.process_chat_question", new_callable=AsyncMock)
    def test_process_question_task_internal_server_error(self, mock_process_chat_question):
        mock_process_chat_question.side_effect = Exception("Some error")
        resource_manager = ResourceManager()

        with self.assertRaises(HTTPException) as context:
            asyncio.run(process_question_task(self.chat_request, self.session_id, resource_manager))

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Internal Server Error")

    @patch("modules.vector_index.vector_utils.chat_processor")
    def test_process_chat_question_success(self, mock_chat_processor):
        mock_chat_processor = MagicMock()
        mock_chat_processor.process_chat_question_with_customer_attribute_identifier.return_value = (
            "message", {"products": [{"product": "example", "code": "123"}]}, "{}", 1
        )

        resource_manager = ResourceManager()

        response = asyncio.run(
            process_chat_question(self.chat_request.question, False, self.session_id, resource_manager))

        self.assertEqual(response[0], "message")
        self.assertEqual(response[1], {"products": [{"product": "example", "code": "123"}]})

    # @patch("modules.vector_index.vector_utils.chat_processor.process_chat_question_with_customer_attribute_identifier", new_callable=AsyncMock)
    # def test_process_chat_question_internal_server_error(self, mock_process_chat_question_with_customer_attribute_identifier):
    #     mock_process_chat_question_with_customer_attribute_identifier.side_effect = Exception("Some error")
    #     resource_manager = ResourceManager()
    #
    #     with self.assertRaises(Exception) as context:
    #         asyncio.run(process_chat_question(self.chat_request.question, False, self.session_id, resource_manager))
    #
    #     self.assertEqual(str(context.exception), "Some error")


if __name__ == "__main__":
    unittest.main()
