import unittest
from unittest.mock import MagicMock, patch


class VideoIndexerServiceTests(unittest.TestCase):
    def _build_service(self):
        with patch("backend.src.services.video_indexer.DefaultAzureCredential"):
            from backend.src.services.video_indexer import VideoIndexerService

            service = VideoIndexerService()
        service.location = "westeurope"
        service.account_id = "account-id"
        service.subscription_id = "subscription-id"
        service.resource_group = "resource-group"
        service.vi_name = "video-indexer"
        return service

    def test_extract_data_combines_transcript_and_ocr(self):
        service = self._build_service()
        vi_payload = {
            "videos": [
                {
                    "insights": {
                        "transcript": [{"text": "hello"}, {"text": "world"}],
                        "ocr": [{"text": "screen one"}, {"text": "screen two"}],
                    }
                }
            ],
            "summarizedInsights": {"duration": {"seconds": 42}},
        }

        result = service.extract_data(vi_payload)

        self.assertEqual(result["transcript"], "hello world")
        self.assertEqual(result["ocr_text"], ["screen one", "screen two"])
        self.assertEqual(result["video_metadata"], {"duration": 42, "platform": "youtube"})

    def test_wait_for_processing_returns_payload_when_processed(self):
        service = self._build_service()
        service.get_access_token = MagicMock(return_value="arm-token")
        service.get_account_token = MagicMock(return_value="vi-token")
        processed_payload = {"state": "Processed", "videos": []}

        with patch("backend.src.services.video_indexer.requests.get") as mock_get:
            mock_get.return_value.json.return_value = processed_payload

            result = service.wait_for_processing("video-123")

        self.assertEqual(result, processed_payload)
        mock_get.assert_called_once()

    def test_wait_for_processing_retries_until_processed(self):
        service = self._build_service()
        service.get_access_token = MagicMock(return_value="arm-token")
        service.get_account_token = MagicMock(return_value="vi-token")

        processing_payload = {"state": "Processing"}
        processed_payload = {"state": "Processed", "videos": []}

        with patch("backend.src.services.video_indexer.requests.get") as mock_get, patch(
            "backend.src.services.video_indexer.time.sleep"
        ) as mock_sleep:
            mock_get.return_value.json.side_effect = [processing_payload, processed_payload]

            result = service.wait_for_processing("video-123")

        self.assertEqual(result, processed_payload)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(30)

    def test_wait_for_processing_raises_for_failed_state(self):
        service = self._build_service()
        service.get_access_token = MagicMock(return_value="arm-token")
        service.get_account_token = MagicMock(return_value="vi-token")

        with patch("backend.src.services.video_indexer.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"state": "Failed"}

            with self.assertRaises(Exception) as context:
                service.wait_for_processing("video-123")

        self.assertEqual(str(context.exception), "Video Indexing Failed in Azure.")

    def test_wait_for_processing_raises_for_quarantined_state(self):
        service = self._build_service()
        service.get_access_token = MagicMock(return_value="arm-token")
        service.get_account_token = MagicMock(return_value="vi-token")

        with patch("backend.src.services.video_indexer.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"state": "Quarantined"}

            with self.assertRaises(Exception) as context:
                service.wait_for_processing("video-123")

        self.assertEqual(
            str(context.exception),
            "Video Quarantined (Copyright/Content Policy Violation).",
        )
