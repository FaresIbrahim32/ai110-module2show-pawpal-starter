from datetime import datetime, date, timedelta
from pawpal_system import (
    CarePlan,
    PetOwner,
    Task,
    TaskType,
    TimeSlot,
    WeeklySchedule,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_task(task_id: str = "t1", hour: int = 8, recurrence: str = None) -> Task:
    t = Task(
        task_id=task_id,
        task_type=TaskType.FEEDING,
        scheduled_time=datetime(2026, 3, 23, hour, 0),
        pet_likes=True,
    )
    if recurrence:
        t.recurrence = recurrence
    return t


def make_owner_with_plan() -> tuple[PetOwner, CarePlan]:
    owner = PetOwner(
        username="test_user",
        password="pass",
        name="Test Owner",
        availability=WeeklySchedule(),
    )
    plan = CarePlan(plan_id="plan-1", plan_date=date(2026, 3, 23))
    owner.add_care_plan(plan)
    return owner, plan


# ── Test 1: Task Completion ───────────────────────────────────────────────────

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = make_task()

    assert task.completed is False   # starts incomplete

    task.mark_complete()

    assert task.completed is True    # now marked done


# ── Test 2: Task Addition ─────────────────────────────────────────────────────

def test_adding_task_increases_count():
    """Adding a task to an owner's care plan should increase the task count by 1."""
    owner, plan = make_owner_with_plan()

    assert len(plan.tasks) == 0     # plan starts empty

    owner.add_task(plan.plan_id, make_task("t1"))

    assert len(plan.tasks) == 1     # one task added


# ── Test 3: Sorting Correctness ───────────────────────────────────────────────

def test_tasks_sorted_chronologically():
    """Tasks added out of order should come back sorted by scheduled_time."""
    _, plan = make_owner_with_plan()

    plan.add_task(make_task("t3", hour=18))  # 6 pm — added first
    plan.add_task(make_task("t1", hour=8))   # 8 am
    plan.add_task(make_task("t2", hour=12))  # noon

    sorted_tasks = sorted(plan.tasks, key=lambda t: t.scheduled_time)
    times = [t.scheduled_time.hour for t in sorted_tasks]

    assert times == [8, 12, 18], f"Expected [8, 12, 18], got {times}"


def test_two_tasks_at_same_time_both_present():
    """Two tasks at identical times should both survive sorting (no deduplication)."""
    _, plan = make_owner_with_plan()

    plan.add_task(make_task("t1", hour=9))
    plan.add_task(make_task("t2", hour=9))  # exact same time

    sorted_tasks = sorted(plan.tasks, key=lambda t: t.scheduled_time)

    assert len(sorted_tasks) == 2, "Both tasks must be present even at the same time"


# ── Test 4: Recurrence Logic ──────────────────────────────────────────────────

def test_daily_recurrence_creates_next_day_task():
    """mark_complete() on a daily task should return a new task 24 h later."""
    task = make_task("t1", hour=8, recurrence="daily")

    next_task = task.mark_complete()

    assert next_task is not None, "Expected a new task for daily recurrence"
    assert next_task.scheduled_time == task.scheduled_time + timedelta(days=1)
    assert next_task.task_type == task.task_type


def test_weekly_recurrence_creates_next_week_task():
    """mark_complete() on a weekly task should return a new task 7 days later."""
    task = make_task("t1", hour=8, recurrence="weekly")

    next_task = task.mark_complete()

    assert next_task is not None, "Expected a new task for weekly recurrence"
    assert next_task.scheduled_time == task.scheduled_time + timedelta(days=7)


def test_no_recurrence_returns_none():
    """mark_complete() on a task with no recurrence attribute should return None."""
    task = make_task("t1")  # no recurrence set

    next_task = task.mark_complete()

    assert next_task is None, "Non-recurring task should not spawn a successor"


# ── Test 5: Conflict Detection ────────────────────────────────────────────────

def test_conflict_flagged_when_owner_has_no_availability():
    """A task scheduled when the owner has no slots should be flagged as conflicted."""
    owner, _ = make_owner_with_plan()
    # owner.availability is an empty WeeklySchedule — no slots defined
    task = make_task("t1", hour=10)

    conflicted = task.check_conflict(owner)

    assert conflicted is True, "Task must be conflicted when owner has no availability"


def test_no_conflict_when_task_falls_within_available_slot():
    """A task inside an owner's available slot should NOT be flagged as conflicted."""
    owner, _ = make_owner_with_plan()

    slot = TimeSlot(
        start=datetime(2026, 3, 23, 8, 0),
        end=datetime(2026, 3, 23, 18, 0),
    )
    owner.availability.add_slot("Monday", slot)   # 2026-03-23 is a Monday

    task = make_task("t1", hour=10)  # 10 am falls inside the slot

    conflicted = task.check_conflict(owner)

    assert conflicted is False, "Task within available slot should not be conflicted"


def test_two_tasks_same_time_both_flagged_when_no_availability():
    """Both tasks at the same time should each be independently flagged as conflicted."""
    owner, _ = make_owner_with_plan()

    t1 = make_task("t1", hour=9)
    t2 = make_task("t2", hour=9)

    assert t1.check_conflict(owner) is True
    assert t2.check_conflict(owner) is True
