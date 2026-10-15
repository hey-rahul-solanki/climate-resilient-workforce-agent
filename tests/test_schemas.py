from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from workforce_agent.locations import list_location_ids, load_location
from workforce_agent.schemas import (
    BreakRequirements,
    Certification,
    CoolingBreak,
    Equipment,
    ExposureType,
    HeatMetric,
    HeatThreshold,
    MissingWeatherAction,
    OperatingHours,
    OperationalConstraint,
    OperationalStatus,
    PolicyAction,
    Priority,
    RuleAction,
    RuleSeverity,
    SafetyPolicy,
    SafetyRule,
    ScheduleAssignment,
    ScheduleDecision,
    ScheduleProposal,
    Site,
    SiteHazard,
    TimeWindow,
    UnscheduledWorkOrder,
    WeatherDataQuality,
    WeatherForecast,
    Worker,
    WorkOrder,
    WorkRestRule,
)

IST = ZoneInfo("Asia/Kolkata")
WINDOW = TimeWindow(
    start=datetime(2026, 5, 12, 6, 0, tzinfo=IST),
    end=datetime(2026, 5, 12, 18, 0, tzinfo=IST),
)


def _worker_payload(**overrides):
    payload = {
        "worker_id": "W-01",
        "name": "Asha Patel",
        "skills": ["mechanical", "confined-space"],
        "certifications": [
            {"name": "confined-space", "expires_at": datetime(2026, 12, 31, tzinfo=IST)}
        ],
        "availability_windows": [WINDOW.model_dump()],
        "break_requirements": {
            "min_break_minutes": 15,
            "max_continuous_work_minutes": 120,
            "cooling_break_minutes": 20,
        },
        "max_shift_duration_minutes": 480,
    }
    payload.update(overrides)
    return payload


def _work_order_payload(**overrides):
    payload = {
        "work_order_id": "WO-100",
        "title": "Replace heat-exchanger gasket",
        "duration_minutes": 180,
        "priority": "high",
        "site_id": "VAD-PLANT-01",
        "required_skills": ["mechanical"],
        "required_certifications": ["hot-work"],
        "min_crew_size": 2,
        "max_crew_size": 3,
        "depends_on": ["WO-090"],
        "required_equipment_ids": ["EQ-CRANE-01"],
        "planning_window": WINDOW.model_dump(),
        "deadline": datetime(2026, 5, 12, 20, 0, tzinfo=IST),
        "exposure_type": "outdoor_heat",
        "expected_exposure_duration_minutes": 150,
        "exposure_windows": [WINDOW.model_dump()],
    }
    payload.update(overrides)
    return payload


def test_worker_requires_skills_availability_and_breaks() -> None:
    worker = Worker.model_validate(_worker_payload())
    assert worker.skills == ["mechanical", "confined-space"]
    assert worker.break_requirements.max_continuous_work_minutes == 120


@pytest.mark.parametrize("missing", ["skills", "availability_windows", "break_requirements"])
def test_worker_missing_required_fields_are_actionable(missing: str) -> None:
    payload = _worker_payload()
    del payload[missing]
    with pytest.raises(ValidationError) as exc:
        Worker.model_validate(payload)
    assert missing in str(exc.value)


def test_site_rejects_unknown_timezone() -> None:
    with pytest.raises(ValidationError, match="unknown IANA timezone"):
        Site(
            site_id="X",
            name="Bad TZ",
            latitude=22.3,
            longitude=73.1,
            timezone="Vadodara/Plant",
            operating_hours=[OperatingHours(weekday=0, start_local=time(6), end_local=time(18))],
            hazards=[SiteHazard.EXTREME_HEAT],
        )


def test_work_order_requires_planning_fields() -> None:
    order = WorkOrder.model_validate(_work_order_payload())
    assert order.duration_minutes == 180
    assert order.min_crew_size == 2
    assert order.depends_on == ["WO-090"]


@pytest.mark.parametrize(
    "missing",
    ["duration_minutes", "priority", "site_id", "required_skills", "min_crew_size", "planning_window", "depends_on"],
)
def test_work_order_does_not_invent_required_defaults(missing: str) -> None:
    payload = _work_order_payload()
    del payload[missing]
    with pytest.raises(ValidationError) as exc:
        WorkOrder.model_validate(payload)
    assert missing in str(exc.value)


def test_work_order_crew_and_self_dependency_are_invalid() -> None:
    with pytest.raises(ValidationError, match="max_crew_size"):
        WorkOrder.model_validate(_work_order_payload(max_crew_size=1, min_crew_size=2))
    with pytest.raises(ValidationError, match="depend on itself"):
        WorkOrder.model_validate(_work_order_payload(depends_on=["WO-100"]))


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        TimeWindow(start=datetime(2026, 5, 12, 6, 0), end=datetime(2026, 5, 12, 18, 0))


def test_equipment_and_schedule_contracts() -> None:
    equipment = Equipment(
        equipment_id="EQ-CRANE-01",
        equipment_type="mobile-crane",
        availability_windows=[WINDOW],
        operational_status=OperationalStatus.AVAILABLE,
        compatible_task_types=["lift", "mechanical"],
        inspection_valid_until=datetime(2026, 8, 1, tzinfo=IST),
    )
    policy = SafetyPolicy(
        policy_id="HEAT-NIOSH-01",
        name="Outdoor heat work-rest",
        version="1.0",
        applies_to_exposure_types=[ExposureType.OUTDOOR_HEAT],
        heat_thresholds=[
            HeatThreshold(
                metric=HeatMetric.APPARENT_TEMPERATURE_C,
                caution_c=32,
                high_c=39,
                prohibitive_c=46,
            )
        ],
        work_rest_rules=[
            WorkRestRule(
                metric=HeatMetric.APPARENT_TEMPERATURE_C,
                min_c=39,
                max_c=46,
                work_minutes=20,
                rest_minutes=40,
                cooling_required=True,
            )
        ],
        max_wind_speed_ms=15,
        max_precipitation_mm=5,
        lightning_prohibits_work=True,
        prohibited_weather_codes=[95, 96, 99],
        missing_weather_action=MissingWeatherAction.BLOCK,
    )
    assignment = ScheduleAssignment(
        assignment_id="A-1",
        work_order_id="WO-100",
        site_id="VAD-PLANT-01",
        worker_ids=["W-01", "W-02"],
        equipment_ids=["EQ-CRANE-01"],
        scheduled_window=WINDOW,
        cooling_breaks=[CoolingBreak(window=WINDOW, reason="apparent temperature above 39C")],
        decision=ScheduleDecision.EXTRA_BREAKS,
        rationale="Insert cooling breaks to keep exposure under policy high threshold.",
    )
    proposal = ScheduleProposal(
        proposal_id="P-1",
        planning_cycle_id="CYCLE-1",
        generated_at=datetime(2026, 5, 11, 18, 0, tzinfo=IST),
        horizon=WINDOW,
        policy_id=policy.policy_id,
        weather_forecast_ids=["F-1"],
        assignments=[assignment],
        unscheduled=[UnscheduledWorkOrder(work_order_id="WO-200", reasons=["crew unavailable"])],
    )
    forecast = WeatherForecast(
        forecast_id="F-1",
        site_id="VAD-PLANT-01",
        issued_at=datetime(2026, 5, 12, 4, 0, tzinfo=IST),
        source="fixture",
        valid_from=WINDOW.start,
        valid_until=WINDOW.end,
        hourly=[],
        quality=WeatherDataQuality(
            is_complete=False,
            is_stale=False,
            covers_requested_window=True,
            missing_variables=["temperature_2m"],
            incomplete_hour_count=0,
            notes=["empty hourly series for schema check"],
        ),
    )
    worker = Worker.model_validate(_worker_payload())
    assert equipment.operational_status is OperationalStatus.AVAILABLE
    assert policy.missing_weather_action is MissingWeatherAction.BLOCK
    assert proposal.assignments[0].decision is ScheduleDecision.EXTRA_BREAKS
    assert forecast.quality.is_complete is False
    assert worker.certifications[0].name == "confined-space"


def test_safety_policy_rejects_allowing_work_without_an_explicit_action() -> None:
    with pytest.raises(ValidationError):
        SafetyPolicy(
            policy_id="X",
            name="X",
            version="1",
            applies_to_exposure_types=[ExposureType.OUTDOOR_HEAT],
            heat_thresholds=[
                HeatThreshold(
                    metric=HeatMetric.TEMPERATURE_C,
                    caution_c=30,
                    high_c=35,
                    prohibitive_c=40,
                )
            ],
            work_rest_rules=[],
            lightning_prohibits_work=True,
            prohibited_weather_codes=[],
            missing_weather_action="allow",  # type: ignore[arg-type]
        )


def test_vadodara_location_catalog_loads() -> None:
    assert "vadodara-gujarat" in list_location_ids()
    location = load_location("vadodara-gujarat")
    assert location.display_name == "Vadodara, Gujarat"
    assert {site.site_id for site in location.sites} == {
        "VAD-PLANT-01",
        "VAD-SUB-02",
        "VAD-PIPE-03",
    }
    assert all(site.timezone == "Asia/Kolkata" for site in location.sites)


def test_break_requirements_and_certifications_are_validated() -> None:
    with pytest.raises(ValidationError):
        BreakRequirements(min_break_minutes=-1, max_continuous_work_minutes=60, cooling_break_minutes=10)
    with pytest.raises(ValidationError, match="timezone-aware"):
        Certification(name="hot-work", expires_at=datetime(2026, 1, 1))


def test_schemas_can_be_imported_from_package_root() -> None:
    from workforce_agent import Equipment as EqRoot
    from workforce_agent import SafetyPolicy as PolicyRoot
    from workforce_agent import Worker as WorkerRoot
    from workforce_agent import WorkOrder as WorkOrderRoot

    assert WorkerRoot is Worker
    assert WorkOrderRoot is WorkOrder
    assert EqRoot is Equipment
    assert PolicyRoot is SafetyPolicy


def test_worker_valid_instantiation_without_certifications() -> None:
    payload = _worker_payload(certifications=[])
    worker = Worker.model_validate(payload)
    assert worker.worker_id == "W-01"
    assert worker.certifications == []
    assert worker.max_shift_duration_minutes == 480


@pytest.mark.parametrize(
    ("override", "expected_err"),
    [
        ({"worker_id": ""}, "worker_id"),
        ({"worker_id": "   "}, "worker_id"),
        ({"name": ""}, "name"),
        ({"skills": []}, "skills"),
        ({"skills": ["mechanical", "  "]}, "skills must not contain blank values"),
        ({"availability_windows": []}, "availability_windows"),
        ({"max_shift_duration_minutes": 0}, "max_shift_duration_minutes"),
        ({"max_shift_duration_minutes": -60}, "max_shift_duration_minutes"),
    ],
)
def test_worker_invalid_fields(override: dict, expected_err: str) -> None:
    payload = _worker_payload(**override)
    with pytest.raises(ValidationError, match=expected_err):
        Worker.model_validate(payload)


def test_work_order_weather_exposed_inference_and_explicit() -> None:
    # 1. Inferred as outdoor_heat -> True
    wo_heat = WorkOrder.model_validate(_work_order_payload(exposure_type="outdoor_heat"))
    assert wo_heat.is_weather_exposed is True

    # 2. Inferred as outdoor_storm -> True
    wo_storm = WorkOrder.model_validate(_work_order_payload(exposure_type="outdoor_storm"))
    assert wo_storm.is_weather_exposed is True

    # 3. Inferred as indoor_controlled -> False
    wo_indoor = WorkOrder.model_validate(
        _work_order_payload(exposure_type="indoor_controlled", expected_exposure_duration_minutes=0)
    )
    assert wo_indoor.is_weather_exposed is False

    # 4. Explicit is_weather_exposed on HEIGHT task
    wo_height_outdoor = WorkOrder.model_validate(
        _work_order_payload(exposure_type="height", is_weather_exposed=True)
    )
    assert wo_height_outdoor.is_weather_exposed is True

    wo_height_indoor = WorkOrder.model_validate(
        _work_order_payload(exposure_type="height", is_weather_exposed=False, expected_exposure_duration_minutes=0)
    )
    assert wo_height_indoor.is_weather_exposed is False


def test_work_order_invalid_weather_exposed_combinations() -> None:
    with pytest.raises(ValidationError, match="cannot have is_weather_exposed=False"):
        WorkOrder.model_validate(
            _work_order_payload(exposure_type="outdoor_heat", is_weather_exposed=False)
        )

    with pytest.raises(ValidationError, match="cannot be weather-exposed"):
        WorkOrder.model_validate(
            _work_order_payload(
                exposure_type="indoor_controlled",
                is_weather_exposed=True,
                expected_exposure_duration_minutes=0,
            )
        )


@pytest.mark.parametrize(
    ("override", "expected_err"),
    [
        ({"work_order_id": ""}, "work_order_id"),
        ({"title": "  "}, "title"),
        ({"site_id": ""}, "site_id"),
        ({"duration_minutes": 0}, "duration_minutes"),
        ({"duration_minutes": -30}, "duration_minutes"),
        ({"min_crew_size": 0}, "min_crew_size"),
        (
            {"expected_exposure_duration_minutes": 200, "duration_minutes": 100},
            "expected_exposure_duration_minutes cannot exceed duration_minutes",
        ),
        ({"expected_exposure_duration_minutes": -10}, "expected_exposure_duration_minutes"),
        ({"required_skills": []}, "required_skills"),
        ({"required_skills": ["   "]}, "list values must not contain blanks"),
    ],
)
def test_work_order_invalid_fields(override: dict, expected_err: str) -> None:
    payload = _work_order_payload(**override)
    with pytest.raises(ValidationError, match=expected_err):
        WorkOrder.model_validate(payload)


def test_equipment_valid_with_and_without_site() -> None:
    eq_with_site = Equipment(
        equipment_id="EQ-CRANE-01",
        equipment_type="mobile-crane",
        availability_windows=[WINDOW],
        operational_status=OperationalStatus.AVAILABLE,
        compatible_task_types=["lift", "mechanical"],
        site_id="VAD-PLANT-01",
    )
    assert eq_with_site.site_id == "VAD-PLANT-01"

    eq_mobile = Equipment(
        equipment_id="EQ-GENERATOR-02",
        equipment_type="portable-generator",
        availability_windows=[WINDOW],
        operational_status=OperationalStatus.AVAILABLE,
        compatible_task_types=["electrical"],
        site_id=None,
    )
    assert eq_mobile.site_id is None


@pytest.mark.parametrize(
    ("kwargs", "expected_err"),
    [
        ({"equipment_id": ""}, "equipment_id"),
        ({"equipment_id": "   "}, "equipment_id"),
        ({"equipment_type": ""}, "equipment_type"),
        ({"site_id": "   "}, "site_id"),
        ({"availability_windows": []}, "availability_windows"),
        ({"compatible_task_types": []}, "compatible_task_types"),
        ({"compatible_task_types": ["lift", "  "]}, "compatible_task_types must not contain blank values"),
        ({"operational_status": "broken"}, "operational_status"),
    ],
)
def test_equipment_invalid_fields(kwargs: dict, expected_err: str) -> None:
    base = {
        "equipment_id": "EQ-01",
        "equipment_type": "crane",
        "availability_windows": [WINDOW],
        "operational_status": OperationalStatus.AVAILABLE,
        "compatible_task_types": ["lift"],
    }
    base.update(kwargs)
    with pytest.raises(ValidationError, match=expected_err):
        Equipment(**base)


def test_safety_policy_configurable_rules_and_operational_constraints() -> None:
    rule1 = SafetyRule(
        rule_id="RULE-HEAT-STOP",
        name="Extreme heat stop-work",
        severity=RuleSeverity.CRITICAL,
        required_action=PolicyAction.STOP_WORK,
        description="Stop all outdoor physical work when heat metric reaches prohibitive threshold.",
        condition="apparent_temperature_c >= 46",
        parameters={"threshold_c": 46},
    )
    rule2 = OperationalConstraint(
        rule_id="OP-MAX-SHIFT",
        name="Maximum heat shift constraint",
        severity=RuleSeverity.WARNING,
        required_action=PolicyAction.REQUIRE_REVIEW,
        description="Shifts in extreme heat must not exceed 6 hours without site manager review.",
        parameters={"max_shift_minutes": 360},
    )
    custom_work_rest = WorkRestRule(
        metric=HeatMetric.APPARENT_TEMPERATURE_C,
        min_c=36,
        max_c=42,
        work_minutes=30,
        rest_minutes=30,
        cooling_required=True,
        severity=RuleSeverity.WARNING,
        required_action=PolicyAction.EXTRA_BREAKS,
    )

    policy = SafetyPolicy(
        policy_id="POL-DEMO-2026",
        name="Custom configurable site policy",
        version="2.0",
        applies_to_exposure_types=[ExposureType.OUTDOOR_HEAT, ExposureType.OUTDOOR_STORM],
        heat_thresholds=[
            HeatThreshold(
                metric=HeatMetric.APPARENT_TEMPERATURE_C,
                caution_c=30,
                high_c=38,
                prohibitive_c=45,
            )
        ],
        work_rest_rules=[custom_work_rest],
        rules=[rule1],
        operational_constraints=[rule2],
        max_wind_speed_ms=18.5,
        max_precipitation_mm=10.0,
        lightning_prohibits_work=True,
        prohibited_weather_codes=[95, 96, 99],
        missing_weather_action=MissingWeatherAction.REQUIRE_REVIEW,
    )

    assert policy.policy_id == "POL-DEMO-2026"
    assert policy.rules[0].severity is RuleSeverity.CRITICAL
    assert policy.rules[0].required_action is PolicyAction.STOP_WORK
    assert policy.operational_constraints[0].required_action is PolicyAction.REQUIRE_REVIEW
    assert policy.work_rest_rules[0].severity is RuleSeverity.WARNING
    assert policy.work_rest_rules[0].required_action is PolicyAction.EXTRA_BREAKS
    assert policy.missing_weather_action is MissingWeatherAction.REQUIRE_REVIEW


@pytest.mark.parametrize(
    ("rule_kwargs", "expected_err"),
    [
        ({"rule_id": ""}, "rule_id"),
        ({"rule_id": "   "}, "rule_id"),
        ({"name": ""}, "name"),
        ({"severity": "catastrophic"}, "severity"),
        ({"required_action": "ignore"}, "required_action"),
    ],
)
def test_safety_rule_invalid_fields(rule_kwargs: dict, expected_err: str) -> None:
    base = {
        "rule_id": "R-1",
        "name": "Check",
        "severity": RuleSeverity.WARNING,
        "required_action": PolicyAction.EXTRA_BREAKS,
    }
    base.update(rule_kwargs)
    with pytest.raises(ValidationError, match=expected_err):
        SafetyRule(**base)


def test_safety_policy_invalid_weather_and_operational_thresholds() -> None:
    base_policy_kwargs = {
        "policy_id": "POL-1",
        "name": "Policy 1",
        "version": "1.0",
        "applies_to_exposure_types": [ExposureType.OUTDOOR_HEAT],
        "heat_thresholds": [
            HeatThreshold(
                metric=HeatMetric.TEMPERATURE_C,
                caution_c=30,
                high_c=35,
                prohibitive_c=40,
            )
        ],
        "work_rest_rules": [],
        "lightning_prohibits_work": True,
        "prohibited_weather_codes": [],
        "missing_weather_action": MissingWeatherAction.BLOCK,
    }

    # 1. Negative precipitation
    with pytest.raises(ValidationError, match="max_precipitation_mm"):
        SafetyPolicy(**{**base_policy_kwargs, "max_precipitation_mm": -1.0})

    # 2. Non-positive wind speed (must be gt=0)
    with pytest.raises(ValidationError, match="max_wind_speed_ms"):
        SafetyPolicy(**{**base_policy_kwargs, "max_wind_speed_ms": 0.0})

    # 3. Blank policy_id
    with pytest.raises(ValidationError, match="policy_id"):
        SafetyPolicy(**{**base_policy_kwargs, "policy_id": "   "})

    # 4. Inverted heat thresholds
    with pytest.raises(ValidationError, match="heat thresholds must increase"):
        HeatThreshold(
            metric=HeatMetric.TEMPERATURE_C,
            caution_c=38,
            high_c=35,
            prohibitive_c=40,
        )

    # 5. Inverted work rest rule band
    with pytest.raises(ValidationError, match="max_c must be greater than min_c"):
        WorkRestRule(
            metric=HeatMetric.TEMPERATURE_C,
            min_c=42,
            max_c=38,
            work_minutes=20,
            rest_minutes=40,
            cooling_required=True,
        )

