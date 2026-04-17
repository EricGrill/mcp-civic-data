"""Tests for structured logging configuration."""

import json
import logging
import os
import unittest


class TestGetLogger(unittest.TestCase):
    """Tests for the get_logger function."""

    def tearDown(self):
        """Clean up loggers between tests."""
        logging.getLogger("test_logger").handlers.clear()
        logging.getLogger("test_another").handlers.clear()

    def test_returns_logger_instance(self):
        """get_logger returns a logging.Logger."""
        from mcp_govt_api.utils.logging import get_logger

        logger = get_logger("test_logger")
        self.assertIsInstance(logger, logging.Logger)

    def test_logger_has_handler(self):
        """Logger should have at least one handler configured."""
        from mcp_govt_api.utils.logging import get_logger

        logger = get_logger("test_logger")
        self.assertGreaterEqual(len(logger.handlers), 1)

    def test_logger_name(self):
        """Logger should use the provided name."""
        from mcp_govt_api.utils.logging import get_logger

        logger = get_logger("test_another")
        self.assertEqual(logger.name, "test_another")

    def test_no_duplicate_handlers(self):
        """Calling get_logger twice should not add duplicate handlers."""
        from mcp_govt_api.utils.logging import get_logger

        logger = get_logger("test_logger")
        handler_count = len(logger.handlers)
        get_logger("test_logger")
        self.assertEqual(len(logger.handlers), handler_count)


class TestLogLevel(unittest.TestCase):
    """Tests for log level configuration via environment variable."""

    def tearDown(self):
        logging.getLogger("test_level").handlers.clear()
        os.environ.pop("LOG_LEVEL", None)

    def test_default_log_level(self):
        """Default log level should be INFO."""
        from mcp_govt_api.utils.config import Config

        cfg = Config()
        self.assertEqual(cfg.log_level, "INFO")

    def test_log_level_from_env(self):
        """LOG_LEVEL environment variable should override the default."""
        os.environ["LOG_LEVEL"] = "debug"
        from mcp_govt_api.utils.config import Config

        cfg = Config()
        self.assertEqual(cfg.log_level, "DEBUG")


class TestJSONFormatter(unittest.TestCase):
    """Tests for JSON log output format."""

    def test_output_is_valid_json(self):
        """Log output should be valid JSON."""
        from mcp_govt_api.utils.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello world",
            args=None,
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        self.assertIsInstance(parsed, dict)

    def test_json_contains_required_fields(self):
        """JSON output should contain timestamp, level, module, and message."""
        from mcp_govt_api.utils.logging import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=None,
            exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        self.assertIn("timestamp", parsed)
        self.assertIn("level", parsed)
        self.assertIn("module", parsed)
        self.assertIn("message", parsed)
        self.assertEqual(parsed["level"], "WARNING")
        self.assertEqual(parsed["message"], "test message")

    def test_json_includes_exception(self):
        """JSON output should include exception info when present."""
        import sys

        from mcp_govt_api.utils.logging import JSONFormatter

        formatter = JSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error occurred",
            args=None,
            exc_info=exc_info,
        )
        parsed = json.loads(formatter.format(record))
        self.assertIn("exception", parsed)
        self.assertIn("ValueError", parsed["exception"])


if __name__ == "__main__":
    unittest.main()
