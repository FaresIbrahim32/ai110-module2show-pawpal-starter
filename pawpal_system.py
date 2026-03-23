from enum import Enum
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ─────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────

class SpeciesCategory(Enum):
    SMALL_PETS = "small_pets"   # cats, dogs
    EQUINE = "equine"           # horses
    LIVESTOCK = "livestock"     # cattle
    ZOO = "zoo"                 # wildlife (lions, tigers, etc.)


class AdoptionStatus(Enum):
    STRAY = "stray"
    ADOPTED = "adopted"
    FROM_PREVIOUS_OWNER = "from_previous_owner"
    BRED = "bred"


class FileFormat(Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"


class AppointmentType(Enum):
    VET = "vet"
    GROOMING = "grooming"
    CHECKUP = "checkup"


class AppointmentStatus(Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TaskType(Enum):
    FEEDING = "feeding"
    WALK = "walk"
    SHOWER = "shower"
    MEDICATION = "medication"
    GROOMING = "grooming"
    PLAY = "play"
    OTHER = "other"


# ─────────────────────────────────────────────
# Supporting Dataclasses
# ─────────────────────────────────────────────

@dataclass
class Condition:
    name: str
    description: str
    source_document: str  # prescription file it came from


@dataclass
class Medication:
    name: str
    dosage: str
    frequency: str   # e.g. "once daily", "twice daily", "every 8 hours"
    start_date: date
    end_date: date


@dataclass
class TimeSlot:
    start: datetime
    end: datetime

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start < other.end and self.end > other.start


@dataclass
class WeeklySchedule:
    available_slots: Dict[str, List[TimeSlot]] = field(default_factory=dict)

    def add_slot(self, day: str, slot: TimeSlot):
        self.available_slots.setdefault(day, []).append(slot)

    def remove_slot(self, day: str, slot: TimeSlot):
        if day in self.available_slots:
            self.available_slots[day].remove(slot)

    def is_available(self, dt: datetime) -> bool:
        day = dt.strftime("%A")
        for slot in self.available_slots.get(day, []):
            if slot.start.time() <= dt.time() <= slot.end.time():
                return True
        return False


@dataclass
class Appointment:
    appointment_id: str
    date_time: datetime
    location: str
    appointment_type: AppointmentType
    notes: str = ""
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    provider: Optional["CareProvider"] = field(default=None, repr=False)

    def cancel(self):
        self.status = AppointmentStatus.CANCELLED

    def complete(self):
        self.status = AppointmentStatus.COMPLETED


@dataclass
class Task:
    """
    A care task in the daily plan.
    Conflict rule:
      - If conflicted with owner's schedule, attempt to reschedule within 3 days.
      - If owner is still unavailable after 3 days, pet gets priority —
        the owner's conflicting appointment is cancelled.
    """
    task_id: str
    task_type: TaskType
    scheduled_time: datetime
    pet_likes: bool          # False = pet dislikes but task is still required (e.g. shower)
    conflicted: bool = False
    completed: bool = False
    notes: str = ""

    def mark_complete(self):
        """Mark this task as done."""
        self.completed = True

    def check_conflict(self, owner: "PetOwner") -> bool:
        """Returns True if this task falls outside the owner's available slots."""
        self.conflicted = not owner.availability.is_available(self.scheduled_time)
        return self.conflicted

    def resolve_conflict(self, owner: "PetOwner") -> Optional[datetime]:
        """
        Try to shift the task into an available slot within the next 3 days,
        keeping the same time-of-day. If no slot is found the owner's appointment
        loses priority — caller is responsible for cancelling it.
        Returns the new datetime if rescheduled, None if pet gets priority.
        """
        for days_offset in range(1, 4):
            candidate = self.scheduled_time + timedelta(days=days_offset)
            if owner.availability.is_available(candidate):
                self.scheduled_time = candidate
                self.conflicted = False
                return candidate
        # Still no free slot after 3 days → pet priority
        return None


@dataclass
class Prescription:
    file_id: str
    file_name: str
    file_format: FileFormat
    upload_date: date
    extracted_text: str = ""
    extracted_conditions: List[Condition] = field(default_factory=list)

    def upload(self, raw_content: bytes):
        """Store raw bytes as extracted text (placeholder until real parser added)."""
        self.extracted_text = raw_content.decode("utf-8", errors="ignore")

    def parse(self) -> List[Condition]:
        """
        Very simple line-by-line parser: treats every non-empty line as a
        condition name.  Replace with a real NLP/regex parser as needed.
        """
        self.extracted_conditions = []
        for line in self.extracted_text.splitlines():
            line = line.strip()
            if line:
                self.extracted_conditions.append(
                    Condition(
                        name=line,
                        description="Extracted from prescription",
                        source_document=self.file_name,
                    )
                )
        return self.extracted_conditions


# ── Allergy → task-type handling map ──────────────────────────────────────────
# Each key is a keyword found in an allergy string.
# Value is a list of (TaskType | None, handling instruction).
# None means the guideline applies to all tasks / general contact.
_ALLERGY_TASK_MAP: Dict[str, List[Tuple[Optional[TaskType], str]]] = {
    "dander": [
        (TaskType.SHOWER,   "wear a dust mask and gloves during bath time"),
        (TaskType.GROOMING, "wear a dust mask; brush pet outdoors if possible"),
        (None,              "wash hands thoroughly after any contact"),
    ],
    "fur": [
        (TaskType.WALK,  "wear long sleeves; change clothes afterwards"),
        (TaskType.PLAY,  "wear long sleeves; avoid touching your face"),
        (None,           "wash hands and change clothes after extended contact"),
    ],
    "saliva": [
        (TaskType.FEEDING, "use a long-handled feeder; avoid direct mouth contact"),
        (None,             "avoid licks; wash any skin contact immediately"),
    ],
    "feathers": [
        (TaskType.GROOMING, "wear gloves and a mask during grooming"),
        (None,              "wear gloves when handling the pet"),
    ],
}

# Medication frequency → list of hours (24 h) when dose should be given
_FREQUENCY_HOURS: Dict[str, List[int]] = {
    "once daily":         [8],
    "twice daily":        [8, 20],
    "three times daily":  [8, 14, 20],
    "every 6 hours":      [6, 12, 18, 0],
    "every 8 hours":      [8, 16, 0],
    "every 12 hours":     [8, 20],
    "every 24 hours":     [8],
    "with meals":         [8, 13, 19],
}


@dataclass
class MedicationScheduleItem:
    """When and how a pet should receive a specific medication."""
    medication: Medication
    administration_time: datetime
    instructions: str       # e.g. "Give 5 mg of Rimadyl with food"


@dataclass
class AllergyGuideline:
    """Safe-handling instruction for a task given the owner has a specific allergy."""
    allergy: str
    handling_instruction: str
    related_task_type: Optional[TaskType] = None   # None = applies to all tasks


@dataclass
class RecommendedPlan:
    """
    A full-day care plan created by a CareProvider and sent to the PetOwner.
    Combines:
      - Tasks with scheduled times
      - Medication schedule derived from the pet's active medications
      - Allergy guidelines derived from the owner's declared allergies
    """
    plan_id: str
    plan_date: date
    pet: "Pet"
    created_by: "CareProvider"
    tasks: List[Task] = field(default_factory=list)
    medication_schedule: List[MedicationScheduleItem] = field(default_factory=list)
    allergy_guidelines: List[AllergyGuideline] = field(default_factory=list)

    def add_task(self, task: Task):
        self.tasks.append(task)

    def build_medication_schedule(self, pet: "Pet"):
        """
        For each medication active on plan_date, generate a MedicationScheduleItem
        per dose time derived from the medication's frequency string.
        """
        self.medication_schedule = []
        active_meds = pet.get_active_medications(self.plan_date)
        for med in active_meds:
            freq_key = med.frequency.lower().strip()
            hours = _FREQUENCY_HOURS.get(freq_key, [8])   # default: once at 8 am
            with_food = "meal" in freq_key or "food" in freq_key
            for hour in hours:
                admin_dt = datetime(
                    self.plan_date.year, self.plan_date.month, self.plan_date.day,
                    hour % 24, 0
                )
                note = f"Give {med.dosage} of {med.name}"
                if with_food:
                    note += " with food"
                self.medication_schedule.append(
                    MedicationScheduleItem(
                        medication=med,
                        administration_time=admin_dt,
                        instructions=note,
                    )
                )

    def build_allergy_guidelines(self, owner: "PetOwner"):
        """
        For each allergy in the owner's list, produce AllergyGuideline entries
        using the keyword map above. Unrecognised allergies get a generic guideline.
        """
        self.allergy_guidelines = []
        for allergy in owner.pet_allergies:
            matched = False
            for keyword, entries in _ALLERGY_TASK_MAP.items():
                if keyword in allergy.lower():
                    matched = True
                    for task_type, instruction in entries:
                        self.allergy_guidelines.append(
                            AllergyGuideline(
                                allergy=allergy,
                                handling_instruction=instruction,
                                related_task_type=task_type,
                            )
                        )
            if not matched:
                self.allergy_guidelines.append(
                    AllergyGuideline(
                        allergy=allergy,
                        handling_instruction="wear gloves and wash hands after contact",
                        related_task_type=None,
                    )
                )


@dataclass
class CarePlan:
    """Owner's working daily plan — editable directly by the owner."""
    plan_id: str
    plan_date: date
    tasks: List[Task] = field(default_factory=list)

    def generate_plan(self, pet: "Pet", owner: "PetOwner"):
        del pet, owner  # TODO: AI scheduling logic using pet conditions, meds, owner availability

    def add_task(self, task: Task):
        self.tasks.append(task)

    def edit_task(self, task_id: str, updated_task: Task):
        for i, t in enumerate(self.tasks):
            if t.task_id == task_id:
                self.tasks[i] = updated_task
                return

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.task_id != task_id]


# ─────────────────────────────────────────────
# Core Entity Classes
# ─────────────────────────────────────────────

@dataclass
class Pet:
    name: str
    species: str
    species_category: SpeciesCategory
    age: int
    adoption_status: AdoptionStatus
    owner: Optional["PetOwner"] = field(default=None, repr=False)
    conditions: List[Condition] = field(default_factory=list)
    medications: List[Medication] = field(default_factory=list)
    appointments: List[Appointment] = field(default_factory=list)
    prescriptions: List[Prescription] = field(default_factory=list)

    # ── Conditions ────────────────────────────────────────────────────────────

    def add_condition(self, condition: Condition):
        self.conditions.append(condition)

    def edit_condition(self, condition_name: str, updated: Condition):
        for i, c in enumerate(self.conditions):
            if c.name == condition_name:
                self.conditions[i] = updated
                return

    def remove_condition(self, condition_name: str):
        self.conditions = [c for c in self.conditions if c.name != condition_name]

    # ── Adoption status ───────────────────────────────────────────────────────

    def set_adoption_status(self, status: AdoptionStatus):
        self.adoption_status = status

    # ── Appointments ──────────────────────────────────────────────────────────

    def add_appointment(self, appointment: Appointment):
        self.appointments.append(appointment)

    def edit_appointment(self, appointment_id: str, updated: Appointment):
        for i, a in enumerate(self.appointments):
            if a.appointment_id == appointment_id:
                self.appointments[i] = updated
                return

    def remove_appointment(self, appointment_id: str):
        self.appointments = [a for a in self.appointments
                             if a.appointment_id != appointment_id]

    def get_upcoming_appointments(self, from_date: Optional[date] = None) -> List[Appointment]:
        """Return scheduled appointments on or after from_date, sorted by time."""
        if from_date is None:
            from_date = date.today()
        upcoming = [
            a for a in self.appointments
            if a.status == AppointmentStatus.SCHEDULED
            and a.date_time.date() >= from_date
        ]
        return sorted(upcoming, key=lambda a: a.date_time)

    # ── Medications ───────────────────────────────────────────────────────────

    def get_active_medications(self, on_date: Optional[date] = None) -> List[Medication]:
        """Return medications whose treatment window covers on_date."""
        if on_date is None:
            on_date = date.today()
        return [m for m in self.medications if m.start_date <= on_date <= m.end_date]

    # ── Prescriptions ─────────────────────────────────────────────────────────

    def add_prescription(self, prescription: Prescription):
        self.prescriptions.append(prescription)

    def upload_prescription(self, prescription: Prescription, raw_content: bytes):
        """Upload file content and immediately parse conditions into the pet's record."""
        prescription.upload(raw_content)
        new_conditions = prescription.parse()
        for condition in new_conditions:
            self.add_condition(condition)
        self.prescriptions.append(prescription)


@dataclass
class PetOwner:
    username: str
    password: str
    name: str
    pet_allergies: List[str] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)
    availability: WeeklySchedule = field(default_factory=WeeklySchedule)
    care_plans: List[CarePlan] = field(default_factory=list)
    recommended_plans: List[RecommendedPlan] = field(default_factory=list)

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> bool:
        return self.username == username and self.password == password

    # ── Pet management ────────────────────────────────────────────────────────

    def add_pet(self, pet: Pet):
        pet.owner = self
        self.pets.append(pet)

    def remove_pet(self, pet_name: str):
        self.pets = [p for p in self.pets if p.name != pet_name]

    def edit_pet_info(self, pet_name: str, **kwargs):
        """Update any attribute on a pet by keyword argument, e.g. age=4."""
        for pet in self.pets:
            if pet.name == pet_name:
                for key, value in kwargs.items():
                    setattr(pet, key, value)
                return

    def _get_pet(self, pet_name: str) -> Optional[Pet]:
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    # ── Appointment management (owner side) ───────────────────────────────────

    def add_appointment(self, pet_name: str, appointment: Appointment):
        pet = self._get_pet(pet_name)
        if pet:
            pet.add_appointment(appointment)

    def edit_appointment(self, pet_name: str, appointment_id: str, updated: Appointment):
        pet = self._get_pet(pet_name)
        if pet:
            pet.edit_appointment(appointment_id, updated)

    def remove_appointment(self, pet_name: str, appointment_id: str):
        pet = self._get_pet(pet_name)
        if pet:
            pet.remove_appointment(appointment_id)

    # ── Allergy management ────────────────────────────────────────────────────

    def add_allergy(self, allergy: str):
        if allergy not in self.pet_allergies:
            self.pet_allergies.append(allergy)

    def remove_allergy(self, allergy: str):
        self.pet_allergies = [a for a in self.pet_allergies if a != allergy]

    # ── Schedule management ───────────────────────────────────────────────────

    def edit_schedule(self, schedule: WeeklySchedule):
        self.availability = schedule

    def remove_schedule(self):
        self.availability = WeeklySchedule()

    # ── Care plan management ──────────────────────────────────────────────────

    def add_care_plan(self, plan: CarePlan):
        self.care_plans.append(plan)

    def add_task(self, plan_id: str, task: Task):
        for plan in self.care_plans:
            if plan.plan_id == plan_id:
                plan.add_task(task)
                return

    def edit_task(self, plan_id: str, task_id: str, updated: Task):
        for plan in self.care_plans:
            if plan.plan_id == plan_id:
                plan.edit_task(task_id, updated)
                return

    def remove_task(self, plan_id: str, task_id: str):
        for plan in self.care_plans:
            if plan.plan_id == plan_id:
                plan.remove_task(task_id)
                return

    # ── Recommended plan inbox ────────────────────────────────────────────────

    def receive_recommended_plan(self, plan: RecommendedPlan):
        """Receive a plan pushed by a CareProvider."""
        self.recommended_plans.append(plan)

    # ── Provider search ───────────────────────────────────────────────────────

    def search_providers(self, species_category: SpeciesCategory,
                         registry: Optional[List["CareProvider"]] = None) -> List["CareProvider"]:
        """
        Filter providers from a registry by species category.
        Pass the app-level list of all CareProvider objects as registry.
        """
        if not registry:
            return []
        return [p for p in registry if species_category in p.species_treated]


@dataclass
class CareClinic:
    clinic_id: str
    name: str
    address: str
    species_treated: List[SpeciesCategory] = field(default_factory=list)


@dataclass
class CareProvider:
    username: str
    password: str
    display_name: str
    species_treated: List[SpeciesCategory] = field(default_factory=list)
    patients: List[Pet] = field(default_factory=list)
    affiliated_clinics: List[CareClinic] = field(default_factory=list)

    # ── Auth ──────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> bool:
        return self.username == username and self.password == password

    # ── Patient management ────────────────────────────────────────────────────

    def add_patient(self, pet: Pet):
        if pet not in self.patients:
            self.patients.append(pet)

    def remove_patient(self, pet_name: str):
        self.patients = [p for p in self.patients if p.name != pet_name]

    # ── Medication management ─────────────────────────────────────────────────

    def add_medication(self, pet: Pet, medication: Medication):
        pet.medications.append(medication)

    def edit_medication(self, pet: Pet, med_name: str, updated: Medication):
        for i, m in enumerate(pet.medications):
            if m.name == med_name:
                pet.medications[i] = updated
                return

    def remove_medication(self, pet: Pet, med_name: str):
        pet.medications = [m for m in pet.medications if m.name != med_name]

    # ── Appointment scheduling ────────────────────────────────────────────────

    def add_appointment(self, pet: Pet, appointment: Appointment,
                        owner: PetOwner) -> bool:
        """
        Schedule an appointment for a pet.
        Owner's existing appointments take priority: if the new provider
        appointment falls within 3 days of any owner-scheduled appointment,
        the provider appointment is cancelled and False is returned.
        """
        for existing in pet.appointments:
            if existing.status == AppointmentStatus.CANCELLED:
                continue
            if abs(appointment.date_time - existing.date_time) <= timedelta(days=3):
                appointment.cancel()
                return False
        appointment.provider = self
        pet.add_appointment(appointment)
        return True

    # ── Recommended plan creation ─────────────────────────────────────────────

    def create_recommended_plan(self, plan_id: str, plan_date: date,
                                pet: Pet, owner: PetOwner) -> RecommendedPlan:
        """
        Build a full-day RecommendedPlan and deliver it to the owner's inbox.
        Steps:
          1. Build medication schedule from pet's active medications.
          2. Build allergy guidelines from owner's declared allergies.
          3. Push the plan to the owner via receive_recommended_plan().
        """
        plan = RecommendedPlan(
            plan_id=plan_id,
            plan_date=plan_date,
            pet=pet,
            created_by=self,
        )
        plan.build_medication_schedule(pet)
        plan.build_allergy_guidelines(owner)
        owner.receive_recommended_plan(plan)
        return plan

    # ── Clinic management ─────────────────────────────────────────────────────

    def add_clinic(self, clinic: CareClinic):
        self.affiliated_clinics.append(clinic)

    def search_clinics(self, species_category: SpeciesCategory) -> List[CareClinic]:
        return [c for c in self.affiliated_clinics
                if species_category in c.species_treated]
