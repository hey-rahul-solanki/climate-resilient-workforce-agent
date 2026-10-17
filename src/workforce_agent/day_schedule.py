"""Read-only selected-day service. Provider integration can replace the fixture source."""
from datetime import date

from workforce_agent.calendar import demo_calendar
from workforce_agent.schemas.calendar import DayCalendarResponse


def get_day_schedule(site_id: str, day: date) -> DayCalendarResponse:
    if site_id != 'VAD-PLANT-01':
        raise KeyError(site_id)
    # This read endpoint never generates proposals or runs an optimizer.
    data = demo_calendar(day, include_suggestions=False)
    for employee in data['employees']:
        employee['team'] = 'Plant operations'
    for activity in data['activities']:
        activity['version'] = 1
        activity['source_event_id'] = f"fixture:{site_id}:{day.isoformat()}:{activity['id']}"
    data['mode'] = 'fixture'
    return DayCalendarResponse.model_validate(data)
