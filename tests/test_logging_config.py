import logging
from disagreement.logging_config import setup_logging


def test_setup_logging_sets_level(tmp_path):
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()
    root_logger.handlers.clear()
    try:
        setup_logging(logging.INFO)
        assert root_logger.level == logging.INFO
        assert root_logger.handlers
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)


def test_setup_logging_file(tmp_path):
    log_file = tmp_path / "test.log"
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()
    root_logger.handlers.clear()
    try:
        setup_logging(logging.WARNING, file=str(log_file))
        logging.warning("hello")
        assert log_file.read_text()
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
