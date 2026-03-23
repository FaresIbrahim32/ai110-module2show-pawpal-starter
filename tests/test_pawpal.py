from datetime import datetime, date
from pawpal_system import (
    CarePlan,
    PetOwner,
    Task,
    TaskType,
    WeeklySchedule,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_task(task_id: str = "t1") -> Task:
    return Task(
        task_id=task_id,
        task_type=TaskType.FEEDING,
        scheduled_time=datetime(2026, 3, 23, 8, 0),
        pet_likes=True,
    )


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
