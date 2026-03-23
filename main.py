from datetime import datetime, date, time

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
# Setup: Owner
# ─────────────────────────────────────────────

# Owner is available Monday–Friday 7 am – 9 pm
schedule = WeeklySchedule()
for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
    slot = TimeSlot(
        start=datetime.combine(date.today(), time(7, 0)),
        end=datetime.combine(date.today(), time(21, 0)),
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
# Setup: Care Plan with Tasks
# ─────────────────────────────────────────────

today = date.today()
plan = CarePlan(plan_id="plan-001", plan_date=today)
owner.add_care_plan(plan)

tasks = [
    Task(
        task_id="t1",
        task_type=TaskType.FEEDING,
        scheduled_time=datetime.combine(today, time(8, 0)),
        pet_likes=True,
        notes="Luna & Rocky — morning kibble",
    ),
    Task(
        task_id="t2",
        task_type=TaskType.WALK,
        scheduled_time=datetime.combine(today, time(11, 30)),
        pet_likes=True,
        notes="Rocky — 30-min park walk",
    ),
    Task(
        task_id="t3",
        task_type=TaskType.SHOWER,
        scheduled_time=datetime.combine(today, time(14, 0)),
        pet_likes=False,
        notes="Luna — monthly bath (wear gloves — cat dander allergy)",
    ),
    Task(
        task_id="t4",
        task_type=TaskType.FEEDING,
        scheduled_time=datetime.combine(today, time(18, 0)),
        pet_likes=True,
        notes="Luna & Rocky — evening meal",
    ),
    Task(
        task_id="t5",
        task_type=TaskType.PLAY,
        scheduled_time=datetime.combine(today, time(19, 30)),
        pet_likes=True,
        notes="Rocky — fetch session in the backyard",
    ),
]

for task in tasks:
    owner.add_task(plan.plan_id, task)

# ─────────────────────────────────────────────
# Check conflicts against owner's schedule
# ─────────────────────────────────────────────

for task in plan.tasks:
    task.check_conflict(owner)

# ─────────────────────────────────────────────
# Print Today's Schedule
# ─────────────────────────────────────────────

TASK_ICONS = {
    TaskType.FEEDING:    "🍽 ",
    TaskType.WALK:       "🦮",
    TaskType.SHOWER:     "🚿",
    TaskType.MEDICATION: "💊",
    TaskType.GROOMING:   "✂️ ",
    TaskType.PLAY:       "🎾",
    TaskType.OTHER:      "📌",
}

print("=" * 52)
print(f"  PawPal+  |  Today's Schedule  |  {today.strftime('%A, %b %d %Y')}")
print(f"  Owner: {owner.name}  |  Pets: {', '.join(p.name for p in owner.pets)}")
print("=" * 52)

for task in sorted(plan.tasks, key=lambda t: t.scheduled_time):
    icon   = TASK_ICONS.get(task.task_type, "📌")
    t_str  = task.scheduled_time.strftime("%I:%M %p")
    label  = task.task_type.value.capitalize()
    status = " ⚠ CONFLICT" if task.conflicted else ""
    liked  = "" if task.pet_likes else "  (pet dislikes — but required)"
    print(f"  {t_str}  {icon}  {label:<12}{status}{liked}")
    print(f"           {task.notes}")
    print()

print("=" * 52)
print(f"  Total tasks: {len(plan.tasks)}")
if owner.pet_allergies:
    print(f"  Allergy reminders: {', '.join(owner.pet_allergies)}")
print("=" * 52)
