from datetime import datetime, date, time, timedelta

from pawpal_system import (
    AdoptionStatus,
    CarePlan,
    Pet,
    PetOwner,
    SpeciesCategory,
    Task,
    TaskType,
    TimeSlot,
    WeeklySchedule,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_time(day, h, m):
    return datetime.combine(day, time(h, m))


TASK_PRIORITY = {
    TaskType.FEEDING: 1,
    TaskType.MEDICATION: 1,
    TaskType.WALK: 2,
    TaskType.GROOMING: 3,
    TaskType.SHOWER: 3,
    TaskType.PLAY: 4,
    TaskType.OTHER: 5,
}


def sort_tasks(tasks):
    """
    Sort tasks by time, conflict status, and priority.
    """
    return sorted(
        tasks,
        key=lambda t: (
            t.scheduled_time,
            not t.conflicted,
            TASK_PRIORITY.get(t.task_type, 99),
        )
    )


# ─────────────────────────────────────────────
# Lightweight Conflict Detection
# ─────────────────────────────────────────────

def detect_conflicts_lightweight(tasks):
    """
    Detects scheduling conflicts without stopping execution.

    A conflict occurs when two tasks share the same scheduled time.
    Marks tasks as conflicted and returns warning messages.

    Args:
        tasks (list[Task]): List of tasks.

    Returns:
        list[str]: Warning messages describing conflicts.
    """
    warnings = []
    seen = {}

    for task in tasks:
        key = task.scheduled_time

        if key in seen:
            other = seen[key]

            task.conflicted = True
            other.conflicted = True

            warnings.append(
                f"⚠️ Conflict: '{task.notes}' AND '{other.notes}' "
                f"at {task.scheduled_time.strftime('%I:%M %p')}"
            )
        else:
            seen[key] = task

    return warnings


# ─────────────────────────────────────────────
# Recurring Task Handler
# ─────────────────────────────────────────────

def handle_task_completion(plan):
    """
    Processes completed tasks and creates the next occurrence
    for recurring tasks.

    Args:
        plan (CarePlan): The care plan containing tasks.
    """
    new_tasks = []

    for task in plan.tasks:
        if getattr(task, "completed", False):
            next_task = task.mark_complete()
            if next_task:
                new_tasks.append(next_task)

    plan.tasks.extend(new_tasks)


# ─────────────────────────────────────────────
# Setup: Owner
# ─────────────────────────────────────────────

schedule = WeeklySchedule()
for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
    slot = TimeSlot(
        start=make_time(date.today(), 7, 0),
        end=make_time(date.today(), 21, 0),
    )
    schedule.add_slot(day, slot)

owner = PetOwner(
    username="fares123",
    password="securepass",
    name="Fares",
    pet_allergies=["cat dander"],
    availability=schedule,
)

# ─────────────────────────────────────────────
# Setup: Pets
# ─────────────────────────────────────────────

luna = Pet(
    name="Luna",
    species="Cat",
    species_category=SpeciesCategory.SMALL_PETS,
    age=3,
    adoption_status=AdoptionStatus.ADOPTED,
)

rocky = Pet(
    name="Rocky",
    species="Dog",
    species_category=SpeciesCategory.SMALL_PETS,
    age=5,
    adoption_status=AdoptionStatus.FROM_PREVIOUS_OWNER,
)

owner.add_pet(luna)
owner.add_pet(rocky)

# ─────────────────────────────────────────────
# Setup: Care Plan
# ─────────────────────────────────────────────

today = date.today()
plan = CarePlan(plan_id="plan-001", plan_date=today)
owner.add_care_plan(plan)

# ─────────────────────────────────────────────
# Tasks (WITH SAME-TIME CONFLICT)
# ─────────────────────────────────────────────

tasks = [
    Task("t1", TaskType.FEEDING, make_time(today, 8, 0), True, "Luna breakfast"),
    Task("t2", TaskType.WALK, make_time(today, 8, 0), True, "Rocky walk"),  # conflict
    Task("t3", TaskType.SHOWER, make_time(today, 14, 0), False, "Luna bath"),
]

# Add recurrence
tasks[0].recurrence = "daily"

for task in tasks:
    owner.add_task(plan.plan_id, task)

# ─────────────────────────────────────────────
# Conflict Detection
# ─────────────────────────────────────────────

warnings = detect_conflicts_lightweight(plan.tasks)

# ─────────────────────────────────────────────
# Simulate Task Completion
# ─────────────────────────────────────────────

tasks[0].completed = True  # complete recurring task
handle_task_completion(plan)

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

TASK_ICONS = {
    TaskType.FEEDING: "🍽 ",
    TaskType.WALK: "🦮 ",
    TaskType.SHOWER: "🚿 ",
    TaskType.MEDICATION: "💊 ",
    TaskType.GROOMING: "✂️ ",
    TaskType.PLAY: "🎾 ",
    TaskType.OTHER: "📌 ",
}

W = 60


def divider(char="─"):
    print(char * W)


def header():
    divider("═")
    print("🐾 PawPal+ · Smart Scheduler")
    print(f"📅 {today.strftime('%A, %B %d %Y')}")
    print(f"👤 Owner: {owner.name}")
    print("🐕 Pets:", ", ".join(p.name for p in owner.pets))
    divider("═")


def print_task(task, i):
    icon = TASK_ICONS.get(task.task_type, "📌 ")
    tstr = task.scheduled_time.strftime("%I:%M %p")

    print(f"{i}. {tstr} {icon} {task.task_type.value}")
    print(f"   📝 {task.notes}")

    if task.conflicted:
        print("   🔴 Conflict detected")

    if not task.pet_likes:
        print("   ⚠️ Pet dislikes this")

    divider()


def footer(tasks):
    print(f"✅ Total tasks: {len(tasks)}")
    if owner.pet_allergies:
        print(f"🤧 Allergies: {', '.join(owner.pet_allergies)}")
    divider("═")


# ─────────────────────────────────────────────
# Render
# ─────────────────────────────────────────────

header()

if warnings:
    print("\n🚨 Scheduling Warnings:")
    for w in warnings:
        print(w)
    divider()

sorted_tasks = sort_tasks(plan.tasks)

for i, task in enumerate(sorted_tasks, 1):
    print_task(task, i)

footer(sorted_tasks)

# ─────────────────────────────────────────────
# Show Recurring Result
# ─────────────────────────────────────────────

print("\n🔁 After Completing Recurring Task:")
for t in plan.tasks:
    print(f"- {t.task_id} → {t.scheduled_time.strftime('%I:%M %p')}")