import unittest
from unittest.mock import MagicMock, patch

from modules.vector_index.vector_utils.chat_processor import process_chat_question_with_customer_attribute_identifier


class TestProcessChatQuestionWithCustomerAttributeIdentifier(unittest.TestCase):

    @patch("time.time")
    @patch("modules.vector_index.vector_utils.chat_processor.extract_customer_attributes")
    @patch("modules.vector_index.vector_utils.chat_processor.split_process_and_message_from_response")
    @patch("modules.vector_index.vector_utils.chat_processor.RetrievalQA.from_chain_type")
    def test_process_chat_question_with_customer_attribute_identifier_success(
            self, mock_from_chain_type, mock_split_process_and_message, mock_extract_attributes, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        mock_llm = MagicMock()
        mock_document = MagicMock()
        mock_retriever = MagicMock()
        mock_document.as_retriever.return_value = mock_retriever
        mock_search_index_get_answer_from_llm = MagicMock()
        mock_from_chain_type.return_value = mock_search_index_get_answer_from_llm
        mock_extract_attributes.return_value = {"attribute": "value"}
        mock_split_process_and_message.return_value = ("message", '{"products": [{"product": "example", "code": "123"}]}')

        question = "What products do you have?"
        document = mock_document
        llm = mock_llm
        chat_history = [{"user": "Hello", "assistant": "Hi"}]

        # Act
        message, product_list_as_json, attributes, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
            question, document, llm, chat_history)

        # Assert
        self.assertEqual(message, "message")
        self.assertEqual(product_list_as_json, {"products": [{"product": "example", "code": "123"}]})
        self.assertEqual(attributes, "{'attribute': 'value'}")
        self.assertEqual(time_to_get_attributes, 1)

    @patch("time.time")
    @patch("modules.vector_index.vector_utils.chat_processor.extract_customer_attributes")
    @patch("modules.vector_index.vector_utils.chat_processor.split_process_and_message_from_response")
    @patch("modules.vector_index.vector_utils.chat_processor.RetrievalQA.from_chain_type")
    def test_process_chat_question_with_customer_attribute_identifier_invalid_chat_history(
            self, mock_from_chain_type, mock_split_process_and_message, mock_extract_attributes, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1, 2]  # Simulating time taken
        mock_llm = MagicMock()
        mock_document = MagicMock()
        mock_retriever = MagicMock()
        mock_document.as_retriever.return_value = mock_retriever
        mock_search_index_get_answer_from_llm = MagicMock()
        mock_from_chain_type.return_value = mock_search_index_get_answer_from_llm
        mock_extract_attributes.return_value = {"attribute": "value"}

        question = "What products do you have?"
        document = mock_document
        llm = mock_llm
        invalid_chat_history = {"user": "Hello", "assistant": "Hi"}  # Invalid type

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            process_chat_question_with_customer_attribute_identifier(question, document, llm, invalid_chat_history)
        self.assertEqual(str(context.exception), "Chat history must be a list of dictionaries.")

    @patch("time.time")
    @patch("modules.vector_index.vector_utils.chat_processor.extract_customer_attributes")
    @patch("modules.vector_index.vector_utils.chat_processor.split_process_and_message_from_response")
    @patch("modules.vector_index.vector_utils.chat_processor.RetrievalQA.from_chain_type")
    def test_process_chat_question_with_customer_attribute_identifier_invalid_chat_history_entry(
            self, mock_from_chain_type, mock_split_process_and_message, mock_extract_attributes, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1, 2]  # Simulating time taken
        mock_llm = MagicMock()
        mock_document = MagicMock()
        mock_retriever = MagicMock()
        mock_document.as_retriever.return_value = mock_retriever
        mock_search_index_get_answer_from_llm = MagicMock()
        mock_from_chain_type.return_value = mock_search_index_get_answer_from_llm
        mock_extract_attributes.return_value = {"attribute": "value"}

        question = "What products do you have?"
        document = mock_document
        llm = mock_llm
        invalid_chat_history = [{"user": "Hello"}]  # Missing 'assistant' key

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            process_chat_question_with_customer_attribute_identifier(question, document, llm, invalid_chat_history)
        self.assertEqual(str(context.exception),
                         "Each entry in chat history must be a dictionary with 'user' and 'assistant' keys.")

    @patch("time.time")
    @patch("modules.vector_index.vector_utils.chat_processor.extract_customer_attributes")
    @patch("modules.vector_index.vector_utils.chat_processor.split_process_and_message_from_response")
    @patch("modules.vector_index.vector_utils.chat_processor.RetrievalQA.from_chain_type")
    def test_process_chat_question_with_customer_attribute_identifier_invalid_json_format(
            self, mock_from_chain_type, mock_split_process_and_message, mock_extract_attributes, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1, 2]  # Simulating time taken
        mock_llm = MagicMock()
        mock_document = MagicMock()
        mock_retriever = MagicMock()
        mock_document.as_retriever.return_value = mock_retriever
        mock_search_index_get_answer_from_llm = MagicMock()
        mock_from_chain_type.return_value = mock_search_index_get_answer_from_llm
        mock_extract_attributes.return_value = {"attribute": "value"}
        mock_split_process_and_message.return_value = ("message", "{'products': [{'product': 'example', 'code': '123'}]}")  # Invalid JSON format

        question = "What products do you have?"
        document = mock_document
        llm = mock_llm
        chat_history = [{"user": "Hello", "assistant": "Hi"}]

        # Act
        message, product_list_as_json, attributes, time_to_get_attributes = process_chat_question_with_customer_attribute_identifier(
            question, document, llm, chat_history)

        # Assert
        self.assertEqual(message, "message")
        self.assertEqual(product_list_as_json, {"products": [{"product": "example", "code": "123"}]})
        self.assertEqual(attributes, "{'attribute': 'value'}")
        self.assertEqual(time_to_get_attributes, 1)

    @patch("time.time")
    @patch("modules.vector_index.vector_utils.chat_processor.extract_customer_attributes")
    @patch("modules.vector_index.vector_utils.chat_processor.split_process_and_message_from_response")
    @patch("modules.vector_index.vector_utils.chat_processor.RetrievalQA.from_chain_type")
    def test_process_chat_question_with_customer_attribute_identifier_access_denied_exception(
            self, mock_from_chain_type, mock_split_process_and_message, mock_extract_attributes, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1, 2]  # Simulating time taken
        mock_llm = MagicMock()
        mock_document = MagicMock()
        mock_retriever = MagicMock()
        mock_document.as_retriever.return_value = mock_retriever
        mock_search_index_get_answer_from_llm = MagicMock()
        mock_from_chain_type.return_value = mock_search_index_get_answer_from_llm
        mock_extract_attributes.side_effect = ValueError("AccessDeniedException")

        question = "What products do you have?"
        document = mock_document
        llm = mock_llm
        chat_history = [{"user": "Hello", "assistant": "Hi"}]

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            process_chat_question_with_customer_attribute_identifier(question, document, llm, chat_history)
        self.assertIn("AccessDeniedException", str(context.exception))


if __name__ == "__main__":
    unittest.main()
