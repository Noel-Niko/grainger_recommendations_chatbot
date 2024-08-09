import unittest
from unittest.mock import patch

from modules.vector_index.vector_utils.response_parser import split_process_and_message_from_response


class TestSplitProcessAndMessageFromResponse(unittest.TestCase):

    @patch("time.time")
    def test_split_process_and_message_from_response_success(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        recs_response = ("<response>Hello, here are the products you requested:</response><products>[{\"product\": "
                         "\"Product A\", \"code\": \"123\"}, {\"product\": \"Product B\", \"code\": "
                         "\"456\"}]</products>")

        # Act
        message, products_json = split_process_and_message_from_response(recs_response)

        # Assert
        expected_message = "Hello, here are the products you requested:"
        expected_products_json = {
            "products": [
                {"product": "Product A", "code": "123"},
                {"product": "Product B", "code": "456"}
            ]
        }
        self.assertEqual(message, expected_message)
        self.assertEqual(products_json, expected_products_json)

    @patch("time.time")
    def test_split_process_and_message_from_response_invalid_json(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        recs_response = "<response>Hello, here are the products you requested:</response><products>{Invalid JSON}</products>"

        # Act
        message, products_json = split_process_and_message_from_response(recs_response)

        # Assert
        self.assertIsNone(message)
        self.assertIsNone(products_json)

    @patch("time.time")
    def test_split_process_and_message_from_response_unexpected_format(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        recs_response = ("<response>Hello, here are the products you requested:</response><productList>[{\"product\": "
                         "\"Product A\", \"code\": \"123\"}]</productList>")

        # Act
        message, products_json = split_process_and_message_from_response(recs_response)

        # Assert
        self.assertIsNone(message)
        self.assertIsNone(products_json)

    @patch("time.time")
    def test_split_process_and_message_from_response_no_products_tag(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        recs_response = "<response>Hello, here are the products you requested:</response>"

        # Act
        message, products_json = split_process_and_message_from_response(recs_response)

        # Assert
        self.assertIsNone(message)
        self.assertIsNone(products_json)

    @patch("time.time")
    def test_split_process_and_message_from_response_no_response_tag(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        recs_response = "<products>[{\"product\": \"Product A\", \"code\": \"123\"}]</products>"

        # Act
        message, products_json = split_process_and_message_from_response(recs_response)

        # Assert
        self.assertIsNone(message)
        expected_products_json = {
            "products": [
                {"product": "Product A", "code": "123"}
            ]
        }
        self.assertEqual(products_json, expected_products_json)

    @patch("time.time")
    def test_split_process_and_message_from_response_empty_products(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        recs_response = "<response>Hello, here are the products you requested:</response><products>[]</products>"

        # Act
        message, products_json = split_process_and_message_from_response(recs_response)

        # Assert
        expected_message = "Hello, here are the products you requested:"
        expected_products_json = {"products": []}
        self.assertEqual(message, expected_message)
        self.assertEqual(products_json, expected_products_json)


if __name__ == "__main__":
    unittest.main()
