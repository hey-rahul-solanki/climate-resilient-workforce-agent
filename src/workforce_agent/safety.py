"""Deterministic climate risk checks for a proposed work window."""

from __future__ import annotations

from math import ceil
from datetime import datetime, timedelta, timezone

from workforce_agent.schemas import (
    ClimateRiskAssessment,
    HeatMetric,
    HourlyWeather,
    MissingWeatherAction,
    SafetyPolicy,
    ScheduleDecision,
    WorkOrder,
    WeatherForecast,
)


def _metric_value(hour: HourlyWeather, metric: HeatMetric) -> float | None:
    return {
        HeatMetric.TEMPERATURE_C: hour.temperature_c,
        HeatMetric.APPARENT_TEMPERATURE_C: hour.apparent_temperature_c,
        HeatMetric.WET_BULB_TEMPERATURE_C: hour.wet_bulb_temperature_c,
    }[metric]


def assess_work_window(
    work_order: WorkOrder,
    policy: SafetyPolicy,
    forecast: WeatherForecast,
    *,
    window_start: datetime | None = None,
) -> ClimateRiskAssessment:
    """Return a conservative policy assessment for a task and forecast window.

    This checks policy thresholds only; it does not determine medical safety or
    replace site emergency procedures.
    """
    start = window_start or work_order.planning_window.start
    end = start + timedelta(minutes=work_order.duration_minutes)
    decision = ScheduleDecision.PROCEED
    reasons: list[str] = []
    cooling_break_minutes = 0
    requires_review = False

    if work_order.exposure_type not in policy.applies_to_exposure_types:
        return ClimateRiskAssessment(
            decision=decision,
            reasons=["policy does not apply to this exposure type"],
            requires_review=False,
            cooling_break_minutes=cooling_break_minutes,
            proposed_window={"start": start, "end": end},
            forecast_id=forecast.forecast_id,
            forecast_issued_at=forecast.issued_at,
        )

    relevant = [h for h in forecast.hourly if start <= h.valid_at < end]
    policy_metrics = {item.metric for item in policy.heat_thresholds}
    policy_metrics.update(item.metric for item in policy.work_rest_rules)
    missing = (
        not relevant
        or forecast.quality.is_stale
        or start < forecast.valid_from
        or end > forecast.valid_until
        or not forecast.quality.covers_requested_window
        or any(hour.missing_fields() for hour in relevant)
        or any(_metric_value(hour, metric) is None for hour in relevant for metric in policy_metrics)
    )
    if missing:
        reasons.append("forecast is missing, stale, or does not cover the proposed work window")
        # A review-required result is not permission to proceed. Keep it blocked
        # until a manager or policy workflow resolves the missing data.
        decision = ScheduleDecision.BLOCKED
        if policy.missing_weather_action == MissingWeatherAction.REQUIRE_REVIEW:
            requires_review = True
            reasons.append("manager review is required before this work can be cleared")

    threshold_by_metric = {item.metric: item for item in policy.heat_thresholds}
    for hour in relevant:
        for metric, thresholds in threshold_by_metric.items():
            value = _metric_value(hour, metric)
            if value is None:
                continue
            if value >= thresholds.prohibitive_c:
                decision = ScheduleDecision.BLOCKED
                reasons.append(f"{metric} {value:g}°C reaches the policy prohibitive threshold")
            elif value >= thresholds.high_c:
                if decision != ScheduleDecision.BLOCKED:
                    decision = ScheduleDecision.RESCHEDULE
                reasons.append(f"{metric} {value:g}°C reaches the policy high threshold")
            elif value >= thresholds.caution_c:
                if decision == ScheduleDecision.PROCEED:
                    decision = ScheduleDecision.EXTRA_BREAKS
                reasons.append(f"{metric} {value:g}°C reaches the policy caution threshold")

        if policy.max_wind_speed_ms is not None and hour.wind_speed_ms is not None:
            if hour.wind_speed_ms > policy.max_wind_speed_ms:
                decision = ScheduleDecision.BLOCKED
                reasons.append("wind speed exceeds the policy maximum")
        if policy.max_precipitation_mm is not None and hour.precipitation_mm is not None:
            if hour.precipitation_mm > policy.max_precipitation_mm:
                decision = ScheduleDecision.BLOCKED
                reasons.append("precipitation exceeds the policy maximum")
        if hour.weather_code in policy.prohibited_weather_codes:
            decision = ScheduleDecision.BLOCKED
            reasons.append(f"weather code {hour.weather_code} is prohibited by policy")
        if policy.lightning_prohibits_work and hour.weather_code in {95, 96, 99}:
            decision = ScheduleDecision.BLOCKED
            reasons.append("forecast indicates thunderstorm conditions")

    for rule in policy.work_rest_rules:
        values = [_metric_value(hour, rule.metric) for hour in relevant]
        values = [value for value in values if value is not None]
        if not values or max(values) < rule.min_c or max(values) >= rule.max_c:
            continue
        if rule.cooling_required or rule.rest_minutes:
            required_breaks = (
                max(1, ceil(work_order.expected_exposure_duration_minutes / rule.work_minutes))
                if rule.work_minutes > 0
                else 1
            )
            cooling_break_minutes += rule.rest_minutes * required_breaks
            if decision == ScheduleDecision.PROCEED:
                decision = ScheduleDecision.EXTRA_BREAKS
            reasons.append(
                f"work-rest policy requires {rule.rest_minutes} minutes of rest per "
                f"{rule.work_minutes} minutes of work ({required_breaks} break(s) for this task)"
            )

    if not reasons:
        reasons.append("forecast conditions are within the configured policy thresholds")

    return ClimateRiskAssessment(
        decision=decision,
        reasons=list(dict.fromkeys(reasons)),
        requires_review=requires_review,
        cooling_break_minutes=cooling_break_minutes,
        proposed_window={"start": start, "end": end},
        forecast_id=forecast.forecast_id,
        forecast_issued_at=forecast.issued_at.astimezone(timezone.utc),
    )
