"""Backward-compatible import for FastAPI planning routes."""
import sys
from calendar_backend import planning_api as _service

sys.modules[__name__] = _service
