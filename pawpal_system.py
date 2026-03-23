from enum import Enum
from datetime import datetime, date
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
class Prescription:
    file_id: str
    file_name: str
    file_format: FileFormat
    upload_date: date
    extracted_text: str = ""
    extracted_conditions: List[Condition] = field(default_factory=list)

    def upload(self, raw_content: bytes):
        pass  # TODO: save file content

    def parse(self) -> List[Condition]:
        pass  # TODO: extract conditions from extracted_text
        return self.extracted_conditions


@dataclass
class PlanTask:
    task_id: str
    description: str
    scheduled_time: datetime
    notes: str = ""


@dataclass
class CarePlan:
    plan_id: str
    plan_date: date
    tasks: List[PlanTask] = field(default_factory=list)

    def generate_plan(self, pet: "Pet", owner: "PetOwner"):
        pass  # TODO: AI scheduling logic using pet conditions, meds, owner availability

    def add_task(self, task: PlanTask):
        self.tasks.append(task)

    def edit_task(self, task_id: str, updated_task: PlanTask):
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

    def search_providers(self, species_category: SpeciesCategory) -> List["CareProvider"]:
        pass  # TODO: query available CareProviders by species category
        return []

    def add_care_plan(self, plan: CarePlan):
        self.care_plans.append(plan)


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
        Add appointment only if it does not conflict with an owner-scheduled
        appointment within 3 days. Owner gets priority within that window.
        """
        from datetime import timedelta
        three_days = timedelta(days=3)
        for existing in pet.appointments:
            if existing.status == AppointmentStatus.CANCELLED:
                continue
            if abs(appointment.date_time - existing.date_time) <= three_days:
                appointment.cancel()
                return False  # conflict — owner appointment takes priority
        appointment.provider = self
        pet.add_appointment(appointment)
        return True

    def add_clinic(self, clinic: CareClinic):
        self.affiliated_clinics.append(clinic)

    def search_clinics(self, species_category: SpeciesCategory) -> List[CareClinic]:
        return [c for c in self.affiliated_clinics
                if species_category in c.species_treated]
