import os
import unittest
from unittest.mock import patch

from backend.src.config import (
    AUDIT_REQUIRED_ENV_VARS,
    ConfigurationError,
    validate_audit_environment,
    validate_required_env,
)


class ConfigValidationTests(unittest.TestCase):
    def test_validate_required_env_lists_missing_values(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError) as context:
                validate_required_env(("FIRST_VAR", "SECOND_VAR"), "test context")

        self.assertEqual(
            str(context.exception),
            "Missing required environment variables for test context: FIRST_VAR, SECOND_VAR",
        )

    def test_validate_audit_environment_passes_with_all_required_values(self):
        fake_env = {name: "configured" for name in AUDIT_REQUIRED_ENV_VARS}

        with patch.dict(os.environ, fake_env, clear=True):
            validate_audit_environment()
