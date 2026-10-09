import logging
import sys
import time
from typing import Optional
from contextlib import contextmanager

# Configure root logger
logger = logging.getLogger("waypoint")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Stream Handler
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(stream_handler)


def get_logger(module_name: str) -> logging.Logger:
    """Returns a namespaced logger."""
    return logging.getLogger(f"waypoint.{module_name}")


@contextmanager
def log_agent_execution(agent_name: str, query: Optional[str] = None):
    """Context manager for tracing agent execution duration and status."""
    log = get_logger(agent_name)
    start_time = time.perf_counter()
    log.info(f"[>] Started {agent_name} {'for query: ' + query if query else ''}")
    try:
        yield
        duration = (time.perf_counter() - start_time) * 1000
        log.info(f"[OK] Completed {agent_name} in {duration:.2f}ms")
    except Exception as e:
        duration = (time.perf_counter() - start_time) * 1000
        log.error(f"[FAIL] Failed {agent_name} after {duration:.2f}ms: {str(e)}", exc_info=True)
        raise e
