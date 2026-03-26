# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| # | Test | What it verifies |
|---|------|-----------------|
| 1 | `test_mark_complete_changes_status` | `mark_complete()` flips `completed` from `False` to `True` |
| 2 | `test_adding_task_increases_count` | Adding a task via `PetOwner.add_task()` grows the plan's task list |
| 3 | `test_tasks_sorted_chronologically` | Tasks added out of order sort correctly by `scheduled_time` |
| 4 | `test_two_tasks_at_same_time_both_present` | No task is silently dropped when two share the exact same time |
| 5 | `test_daily_recurrence_creates_next_day_task` | A daily recurring task generates a successor exactly 24 h later |
| 6 | `test_weekly_recurrence_creates_next_week_task` | A weekly recurring task generates a successor exactly 7 days later |
| 7 | `test_no_recurrence_returns_none` | A task without a recurrence attribute returns `None` on completion |
| 8 | `test_conflict_flagged_when_owner_has_no_availability` | A task is flagged as conflicted when the owner has no availability slots |
| 9 | `test_no_conflict_when_task_falls_within_available_slot` | A task inside a valid availability slot is not flagged |
| 10 | `test_two_tasks_same_time_both_flagged_when_no_availability` | Both same-time tasks are each independently conflict-checked |

### Confidence Level

**★★★★☆ (4 / 5)**

The core scheduling behaviors — sorting, recurrence, and conflict detection — are fully covered and all 10 tests pass. One star is withheld because the `recurrence` attribute is not a declared dataclass field (it must be set manually via `setattr`), which is a fragile contract that future contributors could easily miss. Addressing that in the model would push confidence to 5/5.
