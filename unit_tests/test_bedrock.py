import logging
import os
import sys
import threading
import time
from unittest.mock import patch, MagicMock
import unittest


from modules.vector_index.vector_utils.bedrock import BedrockClientManager
import boto3

from moto import mock_aws

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

# Add project root to sys.path
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)


class TestBedrockClientManager(unittest.TestCase):

    @mock_aws
    def setUp(self):
        self.manager = BedrockClientManager(refresh_interval=1)
        self.session = boto3.Session(region_name="us-east-1")
        self.role_arn = "arn:aws:iam::123456789012:role/TestRole"
        self.client_kwargs = {}

    @mock_aws
    def should_assume_role_and_get_credentials(self):
        with patch.object(self.session, 'client', return_value=MagicMock()) as mock_sts_client:
            mock_sts_client().assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "fake_access_key_id",
                    "SecretAccessKey": "fake_secret_access_key",
                    "SessionToken": "fake_session_token"
                }
            }
            credentials = self.manager.assume_role_and_get_credentials(self.session, self.role_arn)
            self.assertEqual(credentials["AccessKeyId"], "fake_access_key_id")
            self.assertEqual(credentials["SecretAccessKey"], "fake_secret_access_key")
            self.assertEqual(credentials["SessionToken"], "fake_session_token")

    @mock_aws
    def should_update_client_kwargs_with_credentials(self):
        credentials = {
            "AccessKeyId": "fake_access_key_id",
            "SecretAccessKey": "fake_secret_access_key",
            "SessionToken": "fake_session_token"
        }
        self.manager.update_client_kwargs_with_credentials(credentials, self.client_kwargs)
        self.assertEqual(self.client_kwargs["aws_access_key_id"], "fake_access_key_id")
        self.assertEqual(self.client_kwargs["aws_secret_access_key"], "fake_secret_access_key")
        self.assertEqual(self.client_kwargs["aws_session_token"], "fake_session_token")

    @mock_aws
    @patch('modules.vector_index.vector_utils.bedrock.BedrockClientManager.refresh_credentials', autospec=True)
    def should_get_bedrock_client(self, mock_refresh_credentials):
        with patch.object(self.session, 'client', return_value=MagicMock()) as mock_client:
            mock_client().assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "fake_access_key_id",
                    "SecretAccessKey": "fake_secret_access_key",
                    "SessionToken": "fake_session_token"
                }
            }
            os.environ['AWS_REGION'] = 'us-east-1'
            os.environ['BEDROCK_ASSUME_ROLE'] = self.role_arn

            client = self.manager.get_bedrock_client()

            self.assertIsNotNone(client)
            self.assertTrue(mock_refresh_credentials.called)

    @mock_aws
    def should_refresh_credentials(self):
        manager = BedrockClientManager(refresh_interval=3600)
        session = boto3.Session(region_name="us-east-1")
        role_arn = "arn:aws:iam::123456789012:role/TestRole"
        client_kwargs = {}

        mock_credentials = {
            "AccessKeyId": "fake_access_key_id",
            "SecretAccessKey": "fake_secret_access_key",
            "SessionToken": "fake_session_token"
        }
        with patch.object(manager, 'assume_role_and_get_credentials', return_value=mock_credentials), \
                patch.object(manager, 'update_client_kwargs_with_credentials') as mock_update:
            # Call _refresh_once directly
            manager._refresh_once(session, role_arn, client_kwargs)

            # Verify update_client_kwargs_with_credentials was called with the expected arguments
            mock_update.assert_called_once_with(mock_credentials, client_kwargs)


if __name__ == '__main__':
    unittest.main()
