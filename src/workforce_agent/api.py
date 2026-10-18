"""Backward-compatible import for the unified calendar FastAPI service."""
import sys
from calendar_backend import main as _service

sys.modules[__name__] = _service
