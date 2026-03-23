from enum import Enum
from datetime import datetime, date
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
# Supporting Classes
# ─────────────────────────────────────────────

class Condition:
    def __init__(self, name: str, description: str, source_document: str):
        self.name = name
        self.description = description
        self.source_document = source_document  # prescription file it came from


class Medication:
    def __init__(self, name: str, dosage: str, frequency: str,
                 start_date: date, end_date: date):
        self.name = name
        self.dosage = dosage
        self.frequency = frequency
        self.start_date = start_date
        self.end_date = end_date


class TimeSlot:
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start < other.end and self.end > other.start


class WeeklySchedule:
    def __init__(self):
        # key: day name (e.g. "Monday"), value: list of TimeSlots
        self.available_slots: Dict[str, List[TimeSlot]] = {}

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


class Appointment:
    def __init__(self, appointment_id: str, date_time: datetime,
                 location: str, appointment_type: AppointmentType,
                 notes: str = ""):
        self.appointment_id = appointment_id
        self.date_time = date_time
        self.location = location
        self.appointment_type = appointment_type
        self.notes = notes
        self.status = AppointmentStatus.SCHEDULED
        self.provider: Optional["CareProvider"] = None

    def cancel(self):
        self.status = AppointmentStatus.CANCELLED

    def complete(self):
        self.status = AppointmentStatus.COMPLETED


class Prescription:
    def __init__(self, file_id: str, file_name: str, file_format: FileFormat,
                 upload_date: date):
        self.file_id = file_id
        self.file_name = file_name
        self.file_format = file_format
        self.upload_date = upload_date
        self.extracted_text: str = ""
        self.extracted_conditions: List[Condition] = []

    def upload(self, raw_content: bytes):
        pass  # TODO: save file content

    def parse(self) -> List[Condition]:
        pass  # TODO: extract conditions from extracted_text
        return self.extracted_conditions


class PlanTask:
    def __init__(self, task_id: str, description: str,
                 scheduled_time: datetime, notes: str = ""):
        self.task_id = task_id
        self.description = description
        self.scheduled_time = scheduled_time
        self.notes = notes


class CarePlan:
    def __init__(self, plan_id: str, plan_date: date):
        self.plan_id = plan_id
        self.plan_date = plan_date
        self.tasks: List[PlanTask] = []

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
# Core Entities
# ─────────────────────────────────────────────

class Pet:
    def __init__(self, name: str, species: str,
                 species_category: SpeciesCategory, age: int,
                 adoption_status: AdoptionStatus):
        self.name = name
        self.species = species
        self.species_category = species_category
        self.age = age
        self.adoption_status = adoption_status
        self.owner: Optional["PetOwner"] = None
        self.conditions: List[Condition] = []
        self.medications: List[Medication] = []
        self.appointments: List[Appointment] = []
        self.prescriptions: List[Prescription] = []

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


class PetOwner:
    def __init__(self, username: str, password: str, name: str):
        self.username = username
        self.password = password
        self.name = name
        self.pet_allergies: List[str] = []
        self.pets: List[Pet] = []
        self.availability = WeeklySchedule()
        self.care_plans: List[CarePlan] = []

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


class CareClinic:
    def __init__(self, clinic_id: str, name: str, address: str,
                 species_treated: List[SpeciesCategory]):
        self.clinic_id = clinic_id
        self.name = name
        self.address = address
        self.species_treated = species_treated


class CareProvider:
    def __init__(self, username: str, password: str, display_name: str):
        self.username = username
        self.password = password
        self.display_name = display_name
        self.species_treated: List[SpeciesCategory] = []
        self.patients: List[Pet] = []
        self.affiliated_clinics: List[CareClinic] = []

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
            delta = abs((appointment.date_time - existing.date_time))
            if delta <= three_days:
                # Owner priority: cancel provider appointment
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
