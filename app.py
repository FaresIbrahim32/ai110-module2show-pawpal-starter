import streamlit as st
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

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ─────────────────────────────────────────────
# Session state bootstrap
# ─────────────────────────────────────────────

# In-memory registry (no disk). Survives page refreshes while the
# Streamlit server process runs. Lost on server restart.
@st.cache_resource
def owner_registry():
    return {}

registry = owner_registry()

# Optional simple login fields (used to select which owner in the registry)
username = st.sidebar.text_input("Username", value="owner1")
password = st.sidebar.text_input("Password", type="password", value="pass")

if "owner" not in st.session_state:
    schedule = WeeklySchedule()
    for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
        slot = TimeSlot(
            start=datetime.combine(date.today(), time(7, 0)),
            end=datetime.combine(date.today(), time(21, 0)),
        )
        schedule.add_slot(day, slot)

    # Try to load a previously saved owner (by username) from in-memory registry
    loaded = registry.get(username)
    if loaded and loaded.login(username, password):
        st.session_state.owner = loaded
        # restore an active plan reference (use first plan if present)
        if loaded.care_plans:
            st.session_state.plan = loaded.care_plans[0]
        else:
            plan = CarePlan(plan_id="plan-001", plan_date=date.today())
            st.session_state.owner.add_care_plan(plan)
            st.session_state.plan = plan
        st.session_state.task_counter = getattr(st.session_state, "task_counter", 0)
    else:
        # create a fresh owner and save it
        st.session_state.owner = PetOwner(
            username=username,
            password=password,
            name="Your Name",
            availability=schedule,
        )
        plan = CarePlan(plan_id="plan-001", plan_date=date.today())
        st.session_state.owner.add_care_plan(plan)
        st.session_state.plan = plan
        st.session_state.task_counter = 0
        registry[username] = st.session_state.owner

owner: PetOwner = st.session_state.owner
plan: CarePlan  = st.session_state.plan


# Handlers for UI actions
def handle_add_pet(owner: PetOwner, name: str, species: str, cat: str, age: int, status: str):
    new_pet = Pet(
        name=name,
        species=species,
        species_category=SpeciesCategory(cat),
        age=age,
        adoption_status=AdoptionStatus(status),
    )
    owner.add_pet(new_pet)
    registry[owner.username] = owner
    st.sidebar.success(f"{name} added!")


def handle_add_task(owner: PetOwner, plan: CarePlan, task_type_val: str, task_time_val, pet_likes_val: bool, notes_val: str):
    st.session_state.task_counter += 1
    new_task = Task(
        task_id=f"t{st.session_state.task_counter}",
        task_type=TaskType(task_type_val),
        scheduled_time=datetime.combine(date.today(), task_time_val),
        pet_likes=pet_likes_val,
        notes=notes_val,
    )
    new_task.check_conflict(owner)
    owner.add_task(plan.plan_id, new_task)
    registry[owner.username] = owner
    st.success(f"Task '{task_type_val}' added at {task_time_val.strftime('%I:%M %p') }.")

# ─────────────────────────────────────────────
# Sidebar — Add a Pet
# ─────────────────────────────────────────────

st.sidebar.title("PawPal+")
st.sidebar.header("Add a Pet")

with st.sidebar.form("add_pet_form"):
    pet_name    = st.text_input("Pet name")
    pet_species = st.text_input("Species (e.g. Cat, Dog)")
    pet_cat     = st.selectbox("Category", [s.value for s in SpeciesCategory])
    pet_age     = st.number_input("Age", min_value=0, max_value=50, value=1)
    pet_status  = st.selectbox("Adoption status", [s.value for s in AdoptionStatus])
    add_pet_btn = st.form_submit_button("Add Pet")

if add_pet_btn and pet_name:
    handle_add_pet(owner, pet_name, pet_species, pet_cat, pet_age, pet_status)

# ─────────────────────────────────────────────
# Main — Owner summary
# ─────────────────────────────────────────────

st.title("🐾 PawPal+ — Today's Schedule")
st.caption(f"📅 {date.today().strftime('%A, %B %d %Y')}  ·  👤 Owner: {owner.name}")

pet_names = [p.name for p in owner.pets]
if pet_names:
    st.info(f"**Pets registered:** {', '.join(pet_names)}")
else:
    st.warning("No pets yet — add one in the sidebar.")

# ─────────────────────────────────────────────
# Add a Task
# ─────────────────────────────────────────────

st.header("Add a Task")

with st.form("add_task_form"):
    col1, col2 = st.columns(2)
    with col1:
        task_type  = st.selectbox("Task type", [t.value for t in TaskType])
        task_time  = st.time_input("Scheduled time", value=time(8, 0))
    with col2:
        pet_likes  = st.checkbox("Pet likes this task", value=True)
        task_notes = st.text_input("Notes (optional)")
    add_task_btn = st.form_submit_button("Add Task")

if add_task_btn:
    handle_add_task(owner, plan, task_type, task_time, pet_likes, task_notes)

# ─────────────────────────────────────────────
# Today's Schedule
# ─────────────────────────────────────────────

st.header("Today's Schedule")

TASK_ICONS = {
    TaskType.FEEDING:    "🍽",
    TaskType.WALK:       "🦮",
    TaskType.SHOWER:     "🚿",
    TaskType.MEDICATION: "💊",
    TaskType.GROOMING:   "✂️",
    TaskType.PLAY:       "🎾",
    TaskType.OTHER:      "📌",
}

sorted_tasks = sorted(plan.tasks, key=lambda t: t.scheduled_time)

if not sorted_tasks:
    st.info("No tasks yet — add one above.")
else:
    for task in sorted_tasks:
        icon  = TASK_ICONS.get(task.task_type, "📌")
        tstr  = task.scheduled_time.strftime("%I:%M %p")
        label = task.task_type.value.capitalize()

        with st.container():
            col1, col2, col3 = st.columns([2, 5, 2])
            with col1:
                st.markdown(f"**{tstr}**")
            with col2:
                st.markdown(f"{icon} **{label}**")
                if task.notes:
                    st.caption(task.notes)
                if not task.pet_likes:
                    st.warning("Pet dislikes this — but it's required.")
                if task.conflicted:
                    st.error("Conflict with owner schedule — needs rescheduling.")
                if task.completed:
                    st.success("Completed ✓")
            with col3:
                if not task.completed:
                    if st.button("Mark done", key=f"done_{task.task_id}"):
                        task.mark_complete()
                        registry[owner.username] = owner
                        st.rerun()
                if st.button("Remove", key=f"rm_{task.task_id}"):
                    owner.remove_task(plan.plan_id, task.task_id)
                    registry[owner.username] = owner
                    st.rerun()
            st.divider()

    completed = sum(1 for t in plan.tasks if t.completed)
    st.caption(f"✅ {completed}/{len(plan.tasks)} tasks completed")
