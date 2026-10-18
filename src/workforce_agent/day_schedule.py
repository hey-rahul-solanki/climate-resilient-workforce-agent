"""Read-only selected-day and submitted-context services."""
from datetime import date, datetime, timezone

from workforce_agent.calendar import analyze_calendar, demo_calendar
from workforce_agent.schemas import SafetyPolicy, WeatherForecast
from workforce_agent.schemas.calendar import DayCalendarResponse, DayContextSubmission


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


def analyze_submitted_day_context(
    context: DayContextSubmission,
    forecast: WeatherForecast | None,
    policy: SafetyPolicy | None,
    *,
    now: datetime | None = None,
) -> DayCalendarResponse:
    """Apply canonical deterministic warning/freshness analysis to consumer schedule data."""
    if forecast is not None and forecast.site_id != context.site.id:
        raise ValueError('Forecast site differs from the submitted site')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('now must be timezone-aware')

    source_activities = [activity.model_dump(mode='json') for activity in context.activities]
    analysis = analyze_calendar(source_activities, forecast, policy, now=now)
    activities = []
    source_by_id = {activity.id: activity for activity in context.activities}
    for result in analysis['activities']:
        source = source_by_id[result['id']]
        activities.append({
            **result,
            'employee_id': source.employee_id,
            'title': source.title,
            'version': (source.model_extra or {}).get('version', 1),
            'source_event_id': (source.model_extra or {}).get('source_event_id', source.id),
        })
    result = {
        'date': context.date,
        'site': context.site.model_dump(mode='json'),
        'window': context.window.model_dump(mode='json'),
        'employees': [employee.model_dump(mode='json') for employee in context.employees],
        'activities': activities,
        'warnings': analysis['warnings'],
        'suggestions': [],
        'weather': analysis['weather'],
        'integrations': {
            'agent': 'Deterministic climate analysis',
            'mcp': 'Connected',
            'calendar': 'Consumer-submitted; no source writes performed',
        },
        'mode': 'consumer-submitted',
    }
    return DayCalendarResponse.model_validate(result)
