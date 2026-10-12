from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from workforce_agent.locations import load_site
from workforce_agent.schemas import Site, TimeWindow

FIXTURE_DIR = Path(__file__).parent / "fixtures"
OPEN_METEO_FIXTURE = FIXTURE_DIR / "open_meteo_vadodara.json"
IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def plant_site() -> Site:
    return load_site("VAD-PLANT-01", "vadodara-gujarat")


@pytest.fixture
def planning_window() -> TimeWindow:
    return TimeWindow(
        start=datetime(2026, 5, 12, 8, 0, tzinfo=IST),
        end=datetime(2026, 5, 12, 14, 0, tzinfo=IST),
    )
