import unittest

from backend.src.graph.audit_response import parse_audit_response


class AuditResponseParsingTests(unittest.TestCase):
    def test_parse_plain_json_response(self):
        payload = """
        {
            "compliance_results": [],
            "status": "PASS",
            "final_report": "Everything looks safe."
        }
        """

        result = parse_audit_response(payload)

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.final_report, "Everything looks safe.")
        self.assertEqual(result.compliance_results, [])

    def test_parse_fenced_json_response(self):
        payload = """```json
        {
            "compliance_results": [
                {
                    "category": "Unsafe content",
                    "severity": "CRITICAL",
                    "description": "Detected unsafe material."
                }
            ],
            "status": "FAIL",
            "final_report": "Review required."
        }
        ```"""

        result = parse_audit_response(payload)

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(len(result.compliance_results), 1)
        self.assertEqual(result.compliance_results[0].category, "Unsafe content")

    def test_raise_clear_error_for_invalid_json(self):
        with self.assertRaises(ValueError) as context:
            parse_audit_response("not valid json")

        self.assertEqual(
            str(context.exception),
            "LLM returned invalid JSON for the audit response.",
        )

    def test_raise_clear_error_for_missing_required_fields(self):
        payload = """
        {
            "status": "PASS",
            "final_report": "Incomplete response."
        }
        """

        with self.assertRaises(ValueError) as context:
            parse_audit_response(payload)

        self.assertIn("LLM audit response schema validation failed:", str(context.exception))
