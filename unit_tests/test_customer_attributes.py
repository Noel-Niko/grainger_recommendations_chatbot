import unittest
from unittest.mock import MagicMock, patch

from modules.vector_index.vector_utils.customer_attributes import extract_customer_attributes


class TestExtractCustomerAttributes(unittest.TestCase):

    @patch("time.time")
    def test_extract_customer_attributes_success(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        customer_input = "I am from a large enterprise in the manufacturing industry, and we are sustainability focused."
        mock_llm = MagicMock()
        mock_llm.return_value = (
            "<attributes>{\"Industry\": \"Manufacturing\", \"Size\": \"Large Enterprises\", "
            "\"Sustainability Focused\": true}</attributes>"
        )

        # Act
        attributes = extract_customer_attributes(customer_input, mock_llm)

        # Assert
        expected_attributes = {
            "Industry": "Manufacturing",
            "Size": "Large Enterprises",
            "Sustainability Focused": True
        }
        self.assertEqual(attributes, expected_attributes)

    @patch("time.time")
    def test_extract_customer_attributes_invalid_json(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        customer_input = "I am from a large enterprise in the manufacturing industry, and we are sustainability focused."
        mock_llm = MagicMock()
        mock_llm.return_value = "<attributes>{Invalid JSON}</attributes>"

        # Act
        attributes = extract_customer_attributes(customer_input, mock_llm)

        # Assert
        self.assertEqual(attributes, {})

    @patch("time.time")
    def test_extract_customer_attributes_no_entities(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        customer_input = "Hello"
        mock_llm = MagicMock()
        mock_llm.return_value = "<attributes></attributes>"

        # Act
        attributes = extract_customer_attributes(customer_input, mock_llm)

        # Assert
        self.assertEqual(attributes, {})

    @patch("time.time")
    def test_extract_customer_attributes_missing_entities(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        customer_input = "We are a small business."
        mock_llm = MagicMock()
        mock_llm.return_value = "<attributes>{\"Size\": \"Small Businesses\"}</attributes>"

        # Act
        attributes = extract_customer_attributes(customer_input, mock_llm)

        # Assert
        expected_attributes = {"Size": "Small Businesses"}
        self.assertEqual(attributes, expected_attributes)

    @patch("time.time")
    def test_extract_customer_attributes_empty_attributes(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        customer_input = "We are a small business."
        mock_llm = MagicMock()
        mock_llm.return_value = "<attributes>{}</attributes>"

        # Act
        attributes = extract_customer_attributes(customer_input, mock_llm)

        # Assert
        self.assertEqual(attributes, {})

    @patch("time.time")
    def test_extract_customer_attributes_no_attributes_tag(self, mock_time):
        # Arrange
        mock_time.side_effect = [0, 1]  # Simulating time taken
        customer_input = "We are a small business."
        mock_llm = MagicMock()
        mock_llm.return_value = "No attributes found in the input."

        # Act
        attributes = extract_customer_attributes(customer_input, mock_llm)

        # Assert
        self.assertEqual(attributes, {})


if __name__ == "__main__":
    unittest.main()
