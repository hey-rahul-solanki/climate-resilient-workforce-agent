"""Planning-cycle baseline capture and immutable persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from workforce_agent.schemas import (
    BaselineSnapshot,
    PlanningDataset,
    ScheduleAssignment,
    ScheduleMetrics,
    UnscheduledWorkOrder,
)

METRIC_DEFINITION_VERSION = "1"


class BaselineExistsError(Exception):
    """Raised when a planning cycle already has its write-once baseline."""


def evaluate_schedule(
    dataset: PlanningDataset,
    assignments: list[ScheduleAssignment],
    unscheduled: list[UnscheduledWorkOrder],
) -> ScheduleMetrics:
    """Evaluate schedule allocation and duration metrics using the shared definitions."""
    worker_ids = {worker.worker_id for worker in dataset.workers}
    equipment_ids = {equipment.equipment_id for equipment in dataset.equipment}
    work_order_ids = {work_order.work_order_id for work_order in dataset.work_orders}
    for assignment in assignments:
        if assignment.work_order_id not in work_order_ids:
            raise ValueError(f"unknown work order in assignment: '{assignment.work_order_id}'")
        if unknown := set(assignment.worker_ids) - worker_ids:
            raise ValueError(f"unknown workers in assignment: {', '.join(sorted(unknown))}")
        if unknown := set(assignment.equipment_ids) - equipment_ids:
            raise ValueError(f"unknown equipment in assignment: {', '.join(sorted(unknown))}")
    if unknown := {item.work_order_id for item in unscheduled} - work_order_ids:
        raise ValueError(f"unknown unscheduled work orders: {', '.join(sorted(unknown))}")
    return ScheduleMetrics(
        definition_version=METRIC_DEFINITION_VERSION,
        input_work_order_count=len(dataset.work_orders),
        input_worker_count=len(dataset.workers),
        input_equipment_count=len(dataset.equipment),
        assignment_count=len(assignments),
        scheduled_work_order_count=len({item.work_order_id for item in assignments}),
        worker_allocation_count=sum(len(item.worker_ids) for item in assignments),
        equipment_allocation_count=sum(len(item.equipment_ids) for item in assignments),
        scheduled_minutes=sum(
            int((item.scheduled_window.end - item.scheduled_window.start).total_seconds() // 60)
            for item in assignments
        ),
        unscheduled_work_order_count=len(unscheduled),
    )


class PlanningCycleStore:
    """SQLite store whose trigger rules prevent baseline snapshot mutation."""

    def __init__(self, path: Path):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA recursive_triggers = ON")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS baseline_snapshots ("
            "planning_cycle_id TEXT PRIMARY KEY, snapshot_json TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TRIGGER IF NOT EXISTS baseline_snapshots_no_update "
            "BEFORE UPDATE ON baseline_snapshots BEGIN "
            "SELECT RAISE(ABORT, 'baseline snapshots are immutable'); END"
        )
        connection.execute(
            "CREATE TRIGGER IF NOT EXISTS baseline_snapshots_no_delete "
            "BEFORE DELETE ON baseline_snapshots BEGIN "
            "SELECT RAISE(ABORT, 'baseline snapshots are immutable'); END"
        )
        return connection

    def create_baseline(
        self,
        planning_cycle_id: str,
        dataset: PlanningDataset,
        assignments: list[ScheduleAssignment],
        unscheduled: list[UnscheduledWorkOrder],
    ) -> BaselineSnapshot:
        snapshot = BaselineSnapshot(
            snapshot_id=str(uuid4()),
            planning_cycle_id=planning_cycle_id,
            captured_at=datetime.now(UTC),
            dataset=dataset,
            assignments=assignments,
            unscheduled=unscheduled,
            metrics=evaluate_schedule(dataset, assignments, unscheduled),
        )
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO baseline_snapshots (planning_cycle_id, snapshot_json) VALUES (?, ?)",
                    (planning_cycle_id, snapshot.model_dump_json()),
                )
        except sqlite3.IntegrityError as error:
            raise BaselineExistsError(
                f"baseline already exists for planning cycle '{planning_cycle_id}'"
            ) from error
        return snapshot

    def get_baseline(self, planning_cycle_id: str) -> BaselineSnapshot | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT snapshot_json FROM baseline_snapshots WHERE planning_cycle_id = ?",
                (planning_cycle_id,),
            ).fetchone()
        return BaselineSnapshot.model_validate_json(row[0]) if row else None
