import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.src.graph.nodes import audit_content_node


class AuditContentNodeTests(unittest.TestCase):
    def test_returns_fail_report_when_transcript_is_missing(self):
        result = audit_content_node({"transcript": "", "ocr_text": []})

        self.assertEqual(result["final_status"], "FAIL")
        self.assertEqual(
            result["final_report"],
            "Audit skipped because video processing failed (No Transcript).",
        )
        self.assertEqual(result["retrieved_policies"], [])

    def test_returns_system_error_when_model_output_is_invalid(self):
        state = {
            "transcript": "sample transcript",
            "ocr_text": ["sample"],
            "video_metadata": {"duration": 12},
        }
        docs = [SimpleNamespace(page_content="policy excerpt")]

        with patch("backend.src.graph.nodes.AzureChatOpenAI") as llm_cls, patch(
            "backend.src.graph.nodes.AzureOpenAIEmbeddings"
        ), patch("backend.src.graph.nodes.AzureSearch") as search_cls:
            llm_cls.return_value.invoke.return_value = SimpleNamespace(content="not valid json")
            search_cls.return_value.similarity_search.return_value = docs

            result = audit_content_node(state)

        self.assertEqual(result["final_status"], "FAIL")
        self.assertIn("Audit failed due to a system error:", result["final_report"])
        self.assertIn("LLM returned invalid JSON", result["errors"][0])
        self.assertEqual(result["retrieved_policies"], ["policy excerpt"])

    def test_returns_manual_review_result_for_content_filter_errors(self):
        state = {
            "transcript": "sample transcript",
            "ocr_text": ["sample"],
            "video_metadata": {"duration": 12},
        }
        docs = [SimpleNamespace(page_content="policy excerpt")]

        with patch("backend.src.graph.nodes.AzureChatOpenAI") as llm_cls, patch(
            "backend.src.graph.nodes.AzureOpenAIEmbeddings"
        ), patch("backend.src.graph.nodes.AzureSearch") as search_cls:
            llm_cls.return_value.invoke.side_effect = RuntimeError(
                "content_filter triggered for sexual content"
            )
            search_cls.return_value.similarity_search.return_value = docs

            result = audit_content_node(state)

        self.assertEqual(result["final_status"], "FAIL")
        self.assertEqual(result["compliance_results"][0]["category"], "Content Filter Triggered")
        self.assertIn("manual human review", result["final_report"].lower())
        self.assertEqual(result["retrieved_policies"], ["policy excerpt"])
