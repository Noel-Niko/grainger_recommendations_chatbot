import unittest
from unittest.mock import patch, MagicMock
from modules.vector_index.vector_utils.bedrock import BedrockClientManager
import boto3
from moto import mock_sts

class TestBedrockClientManager(unittest.TestCase):

    @mock_sts
    def setUp(self):
        self.manager = BedrockClientManager(refresh_interval=1)
        self.session = boto3.Session(region_name="us-east-1")
        self.role_arn = "arn:aws:iam::123456789012:role/TestRole"
        self.client_kwargs = {}

    @mock_sts
    def test_assume_role_and_get_credentials(self):
        # Mock the STS client
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

    @mock_sts
    def test_update_client_kwargs_with_credentials(self):
        credentials = {
            "AccessKeyId": "fake_access_key_id",
            "SecretAccessKey": "fake_secret_access_key",
            "SessionToken": "fake_session_token"
        }
        self.manager.update_client_kwargs_with_credentials(credentials, self.client_kwargs)
        self.assertEqual(self.client_kwargs["aws_access_key_id"], "fake_access_key_id")
        self.assertEqual(self.client_kwargs["aws_secret_access_key"], "fake_secret_access_key")
        self.assertEqual(self.client_kwargs["aws_session_token"], "fake_session_token")

    @mock_sts
    @patch('bedrock_client_manager.BedrockClientManager.refresh_credentials', autospec=True)
    def test_get_bedrock_client(self, mock_refresh_credentials):
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

    @mock_sts
    def test_refresh_credentials(self):
        credentials = {
            "AccessKeyId": "fake_access_key_id",
            "SecretAccessKey": "fake_secret_access_key",
            "SessionToken": "fake_session_token"
        }
        with patch.object(self.manager, 'assume_role_and_get_credentials', return_value=credentials), \
             patch.object(self.manager, 'update_client_kwargs_with_credentials') as mock_update:

            # Start the refresh thread
            thread = threading.Thread(target=self.manager.refresh_credentials, args=(self.session, self.role_arn, self.client_kwargs))
            thread.start()
            time.sleep(2)  # Wait enough time for the refresh to happen at least once

            mock_update.assert_called_with(credentials, self.client_kwargs)
            thread.join()

if __name__ == '__main__':
    unittest.main()
