"""Backward-compatible import for FastAPI agent routes."""
import sys
from calendar_backend import agent_api as _service

sys.modules[__name__] = _service
