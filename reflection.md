# PawPal+ Project Reflection

## 1. System Design
Three core actions a user must be able to do 
    1. Upload pet prescriptions in file formats (pdf,doc,docx)
    2. Get a recommended plan on a full day of pet care planned out (approximate times of when to do each action)
    3. Add or modify the plan tasks based on sudden changes in schedule

    for this app's backend , we need 2 entities at least , Pet and Pet Owner.

    Pet Owner (User):
        1. User Auth ( username and password)
        2. Number of pets owned ( one user can have many pets) and each pet's name and species
        3. Owner Pet Allergies ( will be in recommended plan on what tasks to do / how to do them)
        4. Availability (fixed schedule every week)
    Pet :
        1. Species (name and catgeory under which they fall) 
        2. Age
        3. Owner_name -> one pet can be owned by only one owner
        4. Adoption status (stray , adopted , from_previous_owner ,etc )
        5. Conditions (any medical history noted obtained from perspcriptions)
        6. Medications (treating any medical conditions)
        7. Upcoming Vet Appointments

    Care Provider: 
        1. User Auth (can log in as care giver and put info about oneslef)
            1.1 name rendered for pet owner on UI
        2. Species treated (equine -> horses , small_pets -> cats and dogs, livestock -> cattle , zoo-> wildlife animals (lions, tigers,etc))
            2.1 One provider can be for multiple species and can treat multiple pets
    Task :
        1. task type ( entered by user) one user can have many tasks
        2. Pet likes or not ( maybe pet doesnt like it but needs to be done (showering))
        3. time ( when it will be done , date and time)
        4. Conflicted or not ( if conflcited wth Owner schedule then reschedule within 3 days if owner still not available , cancel owner's new appointment , pet gets priority)

    Care Clinic: 
        1.Name 
        2.Species treated
            2.1 Care provider can look for and add clinics based on current pet patient
            2.2 some clinics are only for equine , small_pets etc 

    Methods : 

        Pet Owner registers how many pets he/she has . They also disclose any pet allegries they themselves have. They disclose their schedule avaialbility . They can add new pets , remove pets ,,edit pet info ,add appointments , remove appointments , edit appointments , and edit schedule and remove it. They can add/edit/remove condtions and add /edit/remove adoption status . User can search providers for care based on pet species. 

        Care Provider can add/edit/remove pet medications . They can also add appointments but if that appointment is in conflict with Owner appointment within 3 days, cancel it -> Owner gets priority to cancel and resechudle if their new appointments is within 3 days , after that pet gets priority . Provider can add clinic if no clinics avaialbe for current pet patient . Provider can search clinics based on species treated
    
**a. Initial design**

The initial UML design was built around four core entities derived from the system requirements: PetOwner, Pet, CareProvider, and CareClinic. Supporting classes were added to model domain concepts that each entity depends on: Condition, Medication, Appointment, Prescription, WeeklySchedule, CarePlan, and PlanTask. Two enumerations — SpeciesCategory and AdoptionStatus — were introduced to constrain valid values for species groupings and pet adoption states.

Responsibilities assigned to each class:
- **PetOwner**: Handles user authentication, manages their list of pets, stores personal allergy info and weekly availability, and owns the generated care plans.
- **Pet**: Holds all pet-specific data including species, age, adoption status, and links to its conditions, medications, appointments, and prescriptions.
- **Condition**: Represents a medical condition extracted from a parsed prescription document.
- **Medication**: Stores dosage, frequency, and treatment window for a pet's active medications — managed by the CareProvider.
- **Appointment**: Tracks scheduled vet or care visits, with a status field and a reference to the CareProvider. Conflict resolution logic (owner priority within 3 days) is checked against the owner's WeeklySchedule.
- **Prescription**: Represents an uploaded file (PDF, DOC, DOCX) and its parsed text, from which Conditions are extracted.
- **WeeklySchedule**: Stores the owner's fixed weekly time slots and exposes an availability check used during appointment scheduling.
- **CarePlan**: A daily care plan generated for a PetOwner, broken into ordered PlanTask entries with scheduled times.
- **CareProvider**: Handles provider authentication, tracks which species they treat, manages pet medications and appointments, and can search or add clinics.
- **CareClinic**: Stores clinic name, address, and the species categories it serves — used by providers to find appropriate facilities for a given pet.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
