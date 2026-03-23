from enum import Enum
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional


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
    frequency: str
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
    notes: str = ""

    def check_conflict(self, owner: "PetOwner") -> bool:
        """Returns True if this task conflicts with the owner's weekly schedule."""
        self.conflicted = not owner.availability.is_available(self.scheduled_time)
        return self.conflicted

    def resolve_conflict(self, owner: "PetOwner") -> Optional[datetime]:
        """
        Try to find a free slot within the next 3 days.
        If none found, pet gets priority — returns None to signal owner
        appointment should be cancelled by the caller.
        """
        for days_offset in range(1, 4):
            candidate = self.scheduled_time + timedelta(days=days_offset)
            if owner.availability.is_available(candidate):
                self.scheduled_time = candidate
                self.conflicted = False
                return candidate
        # Owner still unavailable after 3 days → pet priority
        return None


@dataclass
class Prescription:
    file_id: str
    file_name: str
    file_format: FileFormat
    upload_date: date
    extracted_text: str = ""
    extracted_conditions: List[Condition] = field(default_factory=list)

    def upload(self, raw_content: bytes):  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError  # TODO: save file content

    def parse(self) -> List[Condition]:
        raise NotImplementedError  # TODO: extract conditions from extracted_text


@dataclass
class MedicationScheduleItem:
    """When and how a pet should take a specific medication."""
    medication: Medication
    administration_time: datetime       # exact time to give the medication
    instructions: str                   # e.g. "with food", "30 min before meal"


@dataclass
class AllergyGuideline:
    """Handling instruction for a task given the owner has a specific pet allergy."""
    allergy: str                        # the owner's allergy (e.g. "cat dander")
    handling_instruction: str           # e.g. "wear gloves", "use hypoallergenic shampoo"
    related_task_type: Optional[TaskType] = None  # which task this guideline applies to


@dataclass
class RecommendedPlan:
    """
    A full-day care plan created by a CareProvider and sent to the PetOwner.
    Built from:
      - Tasks with scheduled times (what to do and when)
      - Pet's active medications → medication schedule (when to administer each med)
      - Owner's pet allergies → allergy guidelines (how to safely handle each task)
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

    def build_medication_schedule(self, pet: "Pet"):  # pyright: ignore[reportUnusedParameter]
        """Populate medication_schedule from the pet's active medications."""
        raise NotImplementedError  # TODO: derive administration times from medication frequency

    def build_allergy_guidelines(self, owner: "PetOwner"):  # pyright: ignore[reportUnusedParameter]
        """Populate allergy_guidelines from the owner's pet_allergies list."""
        raise NotImplementedError  # TODO: map each allergy to safe-handling instructions per task


@dataclass
class CarePlan:
    """Owner's working daily plan — editable by the owner."""
    plan_id: str
    plan_date: date
    tasks: List[Task] = field(default_factory=list)

    def generate_plan(self, pet: "Pet", owner: "PetOwner"):
        _, __ = pet, owner  # TODO: AI scheduling logic using pet conditions, meds, owner availability

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
# Core Entity Dataclasses
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

    def add_condition(self, condition: Condition):
        self.conditions.append(condition)

    def edit_condition(self, condition_name: str, updated: Condition):
        for i, c in enumerate(self.conditions):
            if c.name == condition_name:
                self.conditions[i] = updated
                return

    def remove_condition(self, condition_name: str):
        self.conditions = [c for c in self.conditions if c.name != condition_name]

    def set_adoption_status(self, status: AdoptionStatus):
        self.adoption_status = status

    def add_appointment(self, appointment: Appointment):
        self.appointments.append(appointment)

    def remove_appointment(self, appointment_id: str):
        self.appointments = [a for a in self.appointments
                             if a.appointment_id != appointment_id]

    def add_prescription(self, prescription: Prescription):
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

    def login(self, username: str, password: str) -> bool:
        return self.username == username and self.password == password

    def add_pet(self, pet: Pet):
        pet.owner = self
        self.pets.append(pet)

    def remove_pet(self, pet_name: str):
        self.pets = [p for p in self.pets if p.name != pet_name]

    def edit_pet_info(self, pet_name: str, **kwargs):
        for pet in self.pets:
            if pet.name == pet_name:
                for key, value in kwargs.items():
                    setattr(pet, key, value)
                return

    def edit_schedule(self, schedule: WeeklySchedule):
        self.availability = schedule

    def remove_schedule(self):
        self.availability = WeeklySchedule()

    def add_care_plan(self, plan: CarePlan):
        self.care_plans.append(plan)

    # ── Task management (owner directly manages tasks within a care plan) ──

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

    # ── Recommended plan inbox ──

    def receive_recommended_plan(self, plan: RecommendedPlan):
        """CareProvider pushes a recommended plan to the owner's inbox."""
        self.recommended_plans.append(plan)

    def search_providers(self, species_category: SpeciesCategory) -> List["CareProvider"]:
        pass  # TODO: query available CareProviders by species category
        return []


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

    def login(self, username: str, password: str) -> bool:
        return self.username == username and self.password == password

    def add_medication(self, pet: Pet, medication: Medication):
        pet.medications.append(medication)

    def edit_medication(self, pet: Pet, med_name: str, updated: Medication):
        for i, m in enumerate(pet.medications):
            if m.name == med_name:
                pet.medications[i] = updated
                return

    def remove_medication(self, pet: Pet, med_name: str):
        pet.medications = [m for m in pet.medications if m.name != med_name]

    def add_appointment(self, pet: Pet, appointment: Appointment,
                        owner: PetOwner) -> bool:
        """
        Owner gets priority for scheduling conflicts.
        Provider appointment is cancelled if it conflicts with an existing
        owner appointment within 3 days.
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

    def create_recommended_plan(self, plan_id: str, plan_date: date,
                                pet: Pet, owner: PetOwner) -> RecommendedPlan:
        """
        Build a RecommendedPlan for the owner by:
          1. Accessing pet.medications to generate a medication schedule.
          2. Accessing owner.pet_allergies to generate safe-handling guidelines.
        Then deliver it to the owner's inbox via receive_recommended_plan().
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

    def add_clinic(self, clinic: CareClinic):
        self.affiliated_clinics.append(clinic)

    def search_clinics(self, species_category: SpeciesCategory) -> List[CareClinic]:
        return [c for c in self.affiliated_clinics
                if species_category in c.species_treated]
