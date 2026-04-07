import os
import tempfile
import unittest
from unittest.mock import patch

from backend.src.graph.nodes import index_video_node


class IndexVideoNodeTests(unittest.TestCase):
    def test_downloaded_temp_file_is_deleted_after_successful_indexing(self):
        temp_handle = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = temp_handle.name
        temp_handle.close()

        state = {
            "video_url": "https://www.youtube.com/watch?v=test",
            "video_id": "vid_test1234",
        }

        with patch("backend.src.graph.nodes.VideoIndexerService") as service_cls, patch(
            "backend.src.graph.nodes.tempfile.NamedTemporaryFile"
        ) as named_temp_file:
            named_temp_file.return_value.__enter__.return_value.name = temp_path
            service = service_cls.return_value
            service.download_youtube_video.return_value = temp_path
            service.upload_video.return_value = "azure-video-id"
            service.wait_for_processing.return_value = {
                "videos": [],
                "summarizedInsights": {"duration": {"seconds": 12}},
            }
            service.extract_data.return_value = {
                "transcript": "sample transcript",
                "ocr_text": ["sample"],
                "video_metadata": {"duration": 12, "platform": "youtube"},
            }

            result = index_video_node(state)

        self.assertFalse(os.path.exists(temp_path))
        self.assertEqual(result["transcript"], "sample transcript")

    def test_downloaded_temp_file_is_deleted_after_upload_failure(self):
        temp_handle = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = temp_handle.name
        temp_handle.close()

        state = {
            "video_url": "https://www.youtube.com/watch?v=test",
            "video_id": "vid_test1234",
        }

        with patch("backend.src.graph.nodes.VideoIndexerService") as service_cls, patch(
            "backend.src.graph.nodes.tempfile.NamedTemporaryFile"
        ) as named_temp_file:
            named_temp_file.return_value.__enter__.return_value.name = temp_path
            service = service_cls.return_value
            service.download_youtube_video.return_value = temp_path
            service.upload_video.side_effect = RuntimeError("upload failed")

            result = index_video_node(state)

        self.assertFalse(os.path.exists(temp_path))
        self.assertEqual(result["final_status"], "FAIL")
        self.assertIn("upload failed", result["errors"][0])
