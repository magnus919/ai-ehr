# OpenMedRecord -- Product Requirements Document

| Field              | Value                                      |
|--------------------|--------------------------------------------|
| **Document ID**    | OMR-PRD-2026-001                           |
| **Version**        | 1.1.0                                      |
| **Status**         | Draft                                      |
| **Author**         | OpenMedRecord Product Team                 |
| **Created**        | 2026-02-11                                 |
| **Last Updated**   | 2026-02-11                                 |
| **Classification** | Public                                     |
| **License**        | Apache 2.0                                 |

---

## Document Revision History

| Version | Date       | Author                      | Description              |
|---------|------------|------------------------------|--------------------------|
| 0.1.0   | 2026-02-11 | OpenMedRecord Product Team   | Initial outline          |
| 1.0.0   | 2026-02-11 | OpenMedRecord Product Team   | First complete draft     |
| 1.1.0   | 2026-02-11 | OpenMedRecord Product Team   | Incorporated findings from architecture, security, and tech lead reviews. Added missing epics. Reconciled cross-document inconsistencies. |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision and Goals](#2-product-vision-and-goals)
3. [User Personas](#3-user-personas)
4. [User Stories](#4-user-stories)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Data Requirements](#7-data-requirements)
8. [Integration Requirements](#8-integration-requirements)
9. [Compliance Requirements Matrix](#9-compliance-requirements-matrix)
10. [Release Plan and Phasing](#10-release-plan-and-phasing)

---

## 1. Executive Summary

### 1.1 Purpose

OpenMedRecord is an open-source, enterprise-grade Electronic Health Record (EHR) system purpose-built for healthcare providers operating within the United States. It delivers a modern, cloud-native platform that replaces legacy EHR systems with a standards-based, extensible, and clinician-friendly solution.

### 1.2 Problem Statement

The current EHR market is dominated by proprietary vendors whose products are expensive to license, difficult to customize, and slow to adopt modern interoperability standards. Small and mid-sized healthcare organizations are forced to choose between unaffordable enterprise systems and underpowered alternatives that fail compliance requirements. Clinician burnout attributable to poor EHR usability is a documented crisis, with studies showing physicians spend nearly two hours on EHR documentation for every hour of direct patient care.

### 1.3 Proposed Solution

OpenMedRecord addresses these challenges by providing:

- **Open-source licensing (Apache 2.0)** -- eliminating per-provider licensing fees and enabling community-driven innovation.
- **HIPAA, SOC 2 Type II, and HITRUST CSF compliance** -- meeting the security and privacy requirements of healthcare organizations of all sizes.
- **AWS-native cloud architecture** -- leveraging managed services for reliability, scalability, and operational efficiency while remaining deployable on-premises or in other cloud environments via Docker containers, though some features (KMS, Cognito, HealthLake) require equivalent substitutions outside AWS.
- **FHIR R4 interoperability as a first-class concern** -- implementing US Core Implementation Guide profiles, SMART on FHIR for third-party application integration, and Bulk Data Access for population-health workflows.
- **Clinician-centered UX** -- designed from the ground up with clinician workflow efficiency as the primary design constraint.

### 1.4 Target Market

| Segment | Description |
|---------|-------------|
| Primary | US-based ambulatory clinics, community health centers, and independent physician practices (1--200 providers) |
| Secondary | Small community hospitals and critical access hospitals (up to 100 beds) |
| Tertiary | Academic medical centers and research institutions seeking an extensible, standards-based platform |
| Ecosystem | Health IT developers building SMART on FHIR applications on top of a certified EHR platform |

### 1.5 Key Differentiators

1. **Open source with enterprise-grade compliance** -- the only open-source EHR that simultaneously targets HIPAA, SOC 2, and HITRUST certification.
2. **Modern developer experience** -- RESTful FHIR APIs, event-driven architecture, infrastructure-as-code, and a plugin system for extensibility.
3. **Clinician-first design** -- sub-three-second page loads, keyboard-navigable workflows, one-click note signing, and AI-assisted documentation.
4. **Total cost of ownership** -- 40--60% lower TCO than comparable proprietary systems over a five-year horizon.

---

## 2. Product Vision and Goals

### 2.1 Vision Statement

> To democratize access to world-class electronic health record technology by building the most clinician-friendly, standards-compliant, and extensible open-source EHR platform -- enabling every healthcare organization, regardless of size or budget, to deliver safer and more coordinated patient care.

### 2.2 Mission

Deliver a production-ready, ONC-certifiable EHR platform that healthcare organizations can deploy, customize, and operate with confidence, backed by an active open-source community and optional commercial support.

### 2.3 Strategic Goals

| ID | Goal | Success Metric | Timeline |
|----|------|----------------|----------|
| G-01 | Achieve ONC Health IT Certification (2015 Edition Cures Update) | Certification granted | Phase 2 |
| G-02 | Reach 100 production deployments | Deployment telemetry (opt-in) | 18 months post-GA |
| G-03 | Reduce clinician documentation time by 30% vs. baseline | Pre/post time-motion studies | Phase 2 |
| G-04 | Maintain HIPAA, SOC 2 Type II, and HITRUST CSF compliance | Annual audit reports | Continuous |
| G-05 | Establish an active open-source community | 500+ GitHub stars, 50+ contributors | 12 months post-GA |
| G-06 | Achieve 99.9% platform availability | Uptime monitoring | Phase 1 GA |
| G-07 | Support 10,000 concurrent clinical users per tenant | Load testing | Phase 2 |
| G-08 | Enable a SMART on FHIR app ecosystem | 10+ third-party apps registered | Phase 3 |

### 2.4 Design Principles

1. **Safety first** -- every feature is evaluated against its potential to cause patient harm; clinical decision support and fail-safes are not optional.
2. **Clinician time is sacred** -- minimize clicks, reduce context switches, and surface the right information at the right time.
3. **Standards over custom** -- prefer HL7 FHIR, SNOMED CT, RxNorm, LOINC, ICD-10, and CPT over proprietary data models.
4. **FHIR-First (not FHIR-Native)** -- the system uses a relational data model optimized for clinical workflows with a FHIR R4 facade for interoperability. Internal services use domain-specific models; FHIR translation occurs at the API boundary.
5. **Secure by default** -- encryption at rest and in transit, least-privilege access, and comprehensive audit logging are non-negotiable baseline behaviors.
6. **Composable architecture** -- the system is built from loosely coupled services with well-defined APIs, enabling replacement or extension of any component.
7. **Accessibility is not an afterthought** -- the UI meets WCAG 2.1 AA and is usable by clinicians with disabilities.
8. **Operational transparency** -- structured logging, distributed tracing, and real-time dashboards give operators full visibility.

### 2.5 Success Criteria

The product will be considered successful when:

- It passes ONC Health IT Certification testing.
- At least three independent healthcare organizations operate it in production for six months with zero critical-severity compliance findings.
- Clinician satisfaction scores (measured via System Usability Scale) exceed 68 (industry average) with a target of 75+ within 12 months post-GA, measured via quarterly SUS surveys of active clinical users.
- The open-source community has merged pull requests from at least 20 external contributors.

---

## 3. User Personas

### 3.1 Dr. Sarah Chen -- Physician

| Attribute | Detail |
|-----------|--------|
| **Role** | Board-certified family medicine physician |
| **Setting** | Multi-provider ambulatory clinic |
| **Experience** | 12 years in practice, has used Epic and Athenahealth |
| **Technical skill** | Moderate; uses a smartphone and dictation tools comfortably |
| **Goals** | Complete documentation quickly, access patient history at a glance, place orders without workflow interruption, end the day on time |
| **Frustrations** | Excessive clicking, redundant data entry, slow system response, alert fatigue from irrelevant clinical decision support warnings |
| **Key workflows** | Patient chart review, SOAP note authoring, order entry (medications, labs, imaging), result review, e-prescribing, referral creation |

### 3.2 Maria Lopez, RN -- Nurse

| Attribute | Detail |
|-----------|--------|
| **Role** | Registered nurse in an ambulatory care setting |
| **Setting** | Multi-provider ambulatory clinic |
| **Experience** | 8 years, has used Cerner and eClinicalWorks |
| **Technical skill** | Moderate |
| **Goals** | Efficiently triage patients, document vital signs and assessments, manage medication administration records, coordinate care tasks |
| **Frustrations** | Incomplete handoff information, inability to customize task lists, slow medication reconciliation workflows |
| **Key workflows** | Patient intake, vital signs documentation, medication reconciliation, care task management, patient education documentation, phone triage |

### 3.3 James Rivera -- Medical Assistant

| Attribute | Detail |
|-----------|--------|
| **Role** | Certified medical assistant |
| **Setting** | Primary care clinic |
| **Experience** | 3 years |
| **Technical skill** | Basic to moderate |
| **Goals** | Complete patient intake quickly, capture accurate demographics and insurance, room patients efficiently |
| **Frustrations** | Redundant data entry across screens, complex navigation, unclear required vs. optional fields |
| **Key workflows** | Patient check-in, demographic and insurance verification, vital signs entry, chief complaint capture, appointment scheduling |

### 3.4 Patricia Nakamura -- Administrative Staff

| Attribute | Detail |
|-----------|--------|
| **Role** | Front desk coordinator and billing specialist |
| **Setting** | Multi-specialty clinic |
| **Experience** | 6 years |
| **Technical skill** | Moderate |
| **Goals** | Manage the daily schedule, verify insurance eligibility in real time, minimize claim denials, handle patient communications |
| **Frustrations** | Scheduling conflicts, inability to see provider availability at a glance, manual insurance verification, difficulty generating reports |
| **Key workflows** | Appointment scheduling and rescheduling, insurance eligibility verification, patient registration, billing code review, report generation |

### 3.5 David Park -- Patient

| Attribute | Detail |
|-----------|--------|
| **Role** | Patient |
| **Setting** | Accesses the system via patient portal (web and mobile) |
| **Experience** | Has used MyChart; expects consumer-grade digital experiences |
| **Technical skill** | Moderate |
| **Goals** | View lab results promptly, message his care team, schedule appointments online, access vaccination records, manage prescriptions |
| **Frustrations** | Delayed result availability, inability to schedule appointments outside business hours, confusing medical jargon without explanation |
| **Key workflows** | View health records, send/receive secure messages, request/schedule appointments, view and pay bills, complete pre-visit questionnaires, download immunization records |

### 3.6 Anika Patel -- System Administrator

| Attribute | Detail |
|-----------|--------|
| **Role** | Health IT system administrator |
| **Setting** | Manages EHR infrastructure for a multi-clinic organization |
| **Experience** | 10 years in health IT |
| **Technical skill** | Advanced (Linux, AWS, Terraform, Kubernetes) |
| **Goals** | Maintain system uptime and performance, manage user provisioning, configure clinical workflows, apply updates with zero downtime |
| **Frustrations** | Opaque vendor systems, lack of API access for automation, difficulty troubleshooting issues, manual upgrade processes |
| **Key workflows** | User account management, role and permission configuration, system monitoring and alerting, backup and disaster recovery, upgrade deployment, integration configuration |

### 3.7 Robert Williams -- Compliance Officer

| Attribute | Detail |
|-----------|--------|
| **Role** | HIPAA Privacy and Security Officer |
| **Setting** | Healthcare organization compliance department |
| **Experience** | 15 years in healthcare compliance |
| **Technical skill** | Moderate |
| **Goals** | Ensure HIPAA compliance, manage audit trails, respond to breach investigations, prepare for SOC 2 and HITRUST assessments |
| **Frustrations** | Incomplete audit logs, inability to generate compliance reports on demand, lack of visibility into access patterns |
| **Key workflows** | Audit log review, access report generation, breach investigation, compliance assessment preparation, policy enforcement verification, risk assessment |

---

## 4. User Stories

User stories are organized by epic. Each story follows the format: *"As a [persona], I want to [action] so that [benefit]."* Acceptance criteria are listed beneath each story.

### Epic 1: Patient Management

#### US-PM-001: Patient Registration

**As a** medical assistant, **I want to** register a new patient with their demographic information **so that** they have a record in the system for their visit.

**Acceptance Criteria:**
- The registration form captures: legal name, preferred name, date of birth, sex assigned at birth, gender identity, race, ethnicity, preferred language, SSN (optional, masked), address, phone numbers, email, emergency contact, and preferred pharmacy.
- All required fields are clearly indicated and validated in real time.
- Duplicate detection runs automatically before the record is saved, matching on name + DOB + SSN.
- If a potential duplicate is found, the user is presented with a side-by-side comparison and can merge or create a new record.
- A unique Medical Record Number (MRN) is generated automatically upon record creation.
- The patient record is persisted as a FHIR Patient resource.
- The action is recorded in the audit log with the creating user's identity and timestamp.

#### US-PM-002: Patient Search

**As a** physician, **I want to** search for a patient by name, date of birth, MRN, or phone number **so that** I can quickly access the correct patient's chart.

**Acceptance Criteria:**
- Search returns results within 500 milliseconds for databases of up to 2 million patient records.
- Search supports partial matching on name (prefix, phonetic).
- Results display: patient photo (if available), full name, DOB, MRN, and last visit date.
- The search is scoped to patients the user has a treatment relationship with, unless the user has an explicit "unrestricted search" permission.
- Each search is logged in the audit trail.

#### US-PM-003: Demographic Updates

**As a** administrative staff member, **I want to** update a patient's demographic information (address, phone, insurance) **so that** the record remains current for billing and communication.

**Acceptance Criteria:**
- All demographic fields are editable by users with the appropriate role.
- Changes are versioned; the previous value is retained in the change history.
- Insurance updates trigger a real-time eligibility verification check.
- The patient is optionally notified of the change via the patient portal.

#### US-PM-004: Insurance Management

**As a** administrative staff member, **I want to** add, update, or remove a patient's insurance coverage **so that** claims are submitted to the correct payer.

**Acceptance Criteria:**
- The system supports primary, secondary, and tertiary insurance plans.
- Insurance data includes: payer name, plan name, member ID, group number, subscriber information, effective dates, and copay/coinsurance details.
- Real-time eligibility verification is available via X12 270/271 transactions or payer API.
- Coverage status (active, inactive, pending verification) is clearly displayed on the patient header.

#### US-PM-005: Patient Merge

**As a** system administrator, **I want to** merge duplicate patient records **so that** a patient's complete clinical history is consolidated in a single record.

**Acceptance Criteria:**
- The merge workflow presents a side-by-side comparison of all data in both records.
- The user selects the surviving record and confirms each field resolution.
- All clinical documents, orders, results, and appointments from the non-surviving record are transferred.
- The non-surviving MRN becomes an alias that redirects to the surviving record.
- The merge is logged as a FHIR AuditEvent with both MRNs.
- Merge operations are reversible within a configurable window (default: 72 hours).

#### US-PM-006: Patient Photo Capture

**As a** medical assistant, **I want to** capture a patient's photograph during registration **so that** clinicians can visually confirm patient identity.

**Acceptance Criteria:**
- The system supports webcam capture and file upload (JPEG, PNG).
- Photos are stored with encryption at rest and associated with the Patient FHIR resource.
- The photo is displayed in the patient header and search results.
- Only users with the `patient.photo.write` permission can add or change photos.

---

### Epic 2: Clinical Documentation

#### US-CD-001: SOAP Note Creation

**As a** physician, **I want to** create a SOAP note (Subjective, Objective, Assessment, Plan) for a patient encounter **so that** I can document the clinical encounter in a structured format.

**Acceptance Criteria:**
- The SOAP note editor provides discrete sections for Subjective, Objective, Assessment, and Plan.
- Rich text editing is supported within each section (bold, italic, lists, tables).
- The Assessment section supports ICD-10 code lookup with typeahead.
- The Plan section supports inline order entry (medications, labs, imaging, referrals).
- Auto-save triggers every 30 seconds and on section blur.
- Notes can be saved as "In Progress" or "Complete" (ready for signing).
- The note is persisted as a FHIR DocumentReference with a structured Composition resource.

#### US-CD-002: Clinical Templates

**As a** physician, **I want to** use pre-built and custom documentation templates **so that** I can document common visit types more efficiently.

**Acceptance Criteria:**
- The system ships with templates for: wellness exam, follow-up, urgent visit, and procedure note.
- Users with the `template.manage` permission can create, edit, and share custom templates.
- Templates support smart text macros (e.g., `.vitals` auto-populates the latest vital signs).
- Templates support conditional logic (e.g., show gestational age section only if the patient is pregnant).
- Templates can be associated with appointment types for automatic pre-population.

#### US-CD-003: Note Signing and Authentication

**As a** physician, **I want to** electronically sign a clinical note **so that** the note becomes part of the permanent medical record.

**Acceptance Criteria:**
- Signing requires re-authentication (password or biometric) as a second factor.
- Signed notes are locked; no further edits are permitted without creating an addendum.
- A signed note displays the signer's name, credential, date, and time.
- The signature event is recorded as a FHIR Provenance resource.
- Co-signature workflows are supported for notes authored by residents or advanced practice providers.

#### US-CD-004: Addendum and Amendment

**As a** physician, **I want to** add an addendum to a signed note **so that** I can supplement the record without altering the original documentation.

**Acceptance Criteria:**
- An addendum is visually linked to the original note and clearly labeled.
- The addendum is separately signed and timestamped.
- The original note remains unmodified.
- Amendments (corrections) display both the original and corrected text with a reason for change.

#### US-CD-005: Voice Dictation

**As a** physician, **I want to** dictate clinical notes using speech-to-text **so that** I can document encounters without typing.

**Acceptance Criteria:**
- The system integrates with a HIPAA-compliant speech-to-text service (e.g., AWS Transcribe Medical or Nuance).
- Dictation accuracy meets or exceeds 95% for standard medical terminology.
- Dictated text streams into the active note section in real time.
- The user can edit dictated text inline before signing.
- All audio processing occurs within the HIPAA-compliant boundary; no audio data is stored after transcription unless the user opts in.

#### US-CD-006: Problem List Management

**As a** physician, **I want to** maintain a patient's problem list **so that** active and resolved conditions are tracked over time.

**Acceptance Criteria:**
- Problems are coded using ICD-10-CM with SNOMED CT cross-mapping.
- Each problem has a status (active, resolved, inactive) and onset date.
- Resolving a problem requires a resolution date and optional comment.
- The problem list is persisted as FHIR Condition resources.
- Changes to the problem list are versioned and auditable.

#### US-CD-007: Allergy Documentation

**As a** nurse, **I want to** document a patient's allergies and adverse reactions **so that** clinicians are alerted during order entry.

**Acceptance Criteria:**
- Allergies are coded using RxNorm (medications) and SNOMED CT (environmental/food).
- Reaction type (allergy, intolerance, adverse reaction) and severity (mild, moderate, severe) are captured.
- Specific reactions (e.g., rash, anaphylaxis) are documented using SNOMED CT codes.
- A "No Known Allergies" (NKA) flag can be explicitly set.
- The allergy list is displayed in the patient header and triggers drug-allergy interaction checking during medication ordering.
- Allergies are persisted as FHIR AllergyIntolerance resources.

---

### Epic 3: Order Entry / CPOE

#### US-OE-001: Medication Order Entry

**As a** physician, **I want to** enter a medication order **so that** the patient's prescribed medications are documented and transmitted to the pharmacy.

**Acceptance Criteria:**
- The order form captures: medication (RxNorm coded), dose, route, frequency, duration, quantity, refills, and pharmacy.
- Typeahead search supports both brand and generic names.
- Drug-drug, drug-allergy, and drug-condition interaction checking runs in real time before order signing.
- Interaction alerts are classified by severity (contraindicated, serious, moderate, minor).
- The clinician can override alerts with a documented reason.
- Orders are persisted as FHIR MedicationRequest resources.
- Signed orders are transmitted electronically to the selected pharmacy (via NCPDP SCRIPT).

#### US-OE-002: Laboratory Order Entry

**As a** physician, **I want to** order laboratory tests **so that** diagnostic testing is initiated and results are routed back to the patient's chart.

**Acceptance Criteria:**
- Lab tests are searchable by name or LOINC code.
- The order captures: test name, specimen type, priority (routine, STAT, ASAP), and clinical indication (ICD-10 diagnosis).
- Order sets (predefined groups of tests) are supported (e.g., "Basic Metabolic Panel").
- Duplicate order checking warns if the same test was ordered within a configurable window.
- The order is transmitted to the reference laboratory via HL7v2 ORM message or FHIR ServiceRequest.
- Orders are persisted as FHIR ServiceRequest resources.

#### US-OE-003: Imaging Order Entry

**As a** physician, **I want to** order imaging studies **so that** diagnostic imaging is scheduled and results are returned to the chart.

**Acceptance Criteria:**
- Imaging studies are searchable by name or CPT/RADLEX code.
- The order captures: study type, body site, laterality, priority, clinical indication, and relevant clinical history.
- Appropriate Use Criteria (AUC) consultation is performed for advanced imaging (CT, MRI, PET) as required by CMS.
- The order is transmitted to the radiology department or external imaging center.
- Orders are persisted as FHIR ServiceRequest resources.

#### US-OE-004: Referral Order Entry

**As a** physician, **I want to** create a referral order **so that** the patient is referred to a specialist with relevant clinical context.

**Acceptance Criteria:**
- The referral captures: referred-to provider, specialty, clinical reason, urgency, and relevant clinical documents.
- The system suggests specialists based on the patient's insurance network.
- The referral order is shareable via Direct messaging or FHIR-based referral exchange.
- Referral status tracking (pending, accepted, scheduled, completed) is visible to the originating provider.
- Referrals are persisted as FHIR ServiceRequest resources.

#### US-OE-005: Order Sets

**As a** physician, **I want to** use predefined order sets **so that** I can efficiently place a group of related orders for common clinical scenarios.

**Acceptance Criteria:**
- Order sets are configurable by clinical leadership and can include medications, labs, imaging, and nursing orders.
- Individual orders within a set can be selected or deselected.
- Order sets support conditional logic (e.g., if creatinine > 1.5, add renal dosing adjustment).
- Order sets are versioned; changes are auditable and require approval.

---

### Epic 4: Medication Management

#### US-MM-001: E-Prescribing

**As a** physician, **I want to** transmit prescriptions electronically to the patient's pharmacy **so that** the prescription is ready for pickup without paper or fax.

**Acceptance Criteria:**
- The system is certified for EPCS (Electronic Prescribing of Controlled Substances) per DEA requirements.
- EPCS requires two-factor authentication using an approved identity-proofing process.
- Prescriptions are transmitted via NCPDP SCRIPT 2017071 (or later).
- The system receives and displays pharmacy fill/refill notifications (RxFill).
- Prescription status (sent, received, filled, partially filled, cancelled) is tracked and visible in the medication list.

#### US-MM-002: Drug Interaction Checking

**As a** physician, **I want to** be alerted to drug-drug and drug-allergy interactions at the point of prescribing **so that** I can avoid prescribing harmful combinations.

**Acceptance Criteria:**
- Interaction checking uses a clinically validated drug knowledge base (e.g., First Databank, Medi-Span).
- Interactions are categorized: contraindicated (must not co-prescribe), serious (usually avoid), moderate (use with caution), minor (informational).
- Contraindicated interactions require a hard stop with documented override justification.
- The system checks interactions against the patient's full active medication list, including external medications (from pharmacy fill history).
- Drug-allergy interactions are displayed with the documented allergy reaction and severity.

#### US-MM-003: Formulary Checking

**As a** physician, **I want to** see whether a medication is on the patient's insurance formulary **so that** I can prescribe cost-effective medications.

**Acceptance Criteria:**
- Formulary data is retrieved in real time from the patient's payer via NCPDP Real-Time Prescription Benefit (RTPB) or equivalent.
- The formulary tier (preferred, non-preferred, specialty) and estimated patient cost are displayed during order entry.
- Formulary alternatives are suggested when the selected medication is non-preferred.
- If formulary data is unavailable, the system displays a clear notification rather than blocking the order.

#### US-MM-004: Medication Reconciliation

**As a** nurse, **I want to** reconcile a patient's medication list during intake **so that** the medication list accurately reflects what the patient is actually taking.

**Acceptance Criteria:**
- The reconciliation workflow presents the current EHR medication list alongside patient-reported medications.
- External medication sources (pharmacy fill data via Surescripts, patient portal input) are displayed for comparison.
- Each medication can be marked as: continued, discontinued, modified, or new.
- The reconciliation event is timestamped, attributed to the reconciling user, and persisted.
- Unreconciled medications are flagged and visible on the patient chart.

#### US-MM-005: Medication Administration Record (MAR)

**As a** nurse, **I want to** document medication administration **so that** there is an accurate record of medications given to the patient.

**Acceptance Criteria:**
- The MAR displays scheduled medications with administration times.
- Barcode scanning of the medication and patient wristband is supported for verification.
- Administration status options: given, held, refused, not given (with reason).
- Late administrations trigger an alert based on configurable thresholds.
- Administrations are persisted as FHIR MedicationAdministration resources.

---

### Epic 5: Scheduling

#### US-SC-001: Appointment Scheduling

**As a** administrative staff member, **I want to** schedule a patient appointment **so that** the patient has a confirmed time to see their provider.

**Acceptance Criteria:**
- The scheduling view displays provider availability in daily, weekly, and monthly views.
- Appointments are created with: patient, provider, appointment type, date/time, duration, location, and reason for visit.
- The system prevents double-booking unless the provider's schedule allows overbooking.
- Appointment confirmation is sent automatically via patient-preferred channel (SMS, email, or portal notification).
- Appointments are persisted as FHIR Appointment resources.

#### US-SC-002: Appointment Rescheduling and Cancellation

**As a** administrative staff member, **I want to** reschedule or cancel a patient appointment **so that** the schedule accurately reflects planned visits.

**Acceptance Criteria:**
- Rescheduling preserves the original appointment's context (reason, linked orders).
- Cancellation requires a reason code (patient no-show, patient request, provider unavailable, etc.).
- Cancelled time slots are automatically released to the waitlist and open scheduling.
- Notification of the change is sent to the patient and provider.

#### US-SC-003: Patient Self-Scheduling

**As a** patient, **I want to** schedule, reschedule, or cancel appointments through the patient portal **so that** I can manage my healthcare appointments without calling the office.

**Acceptance Criteria:**
- Self-scheduling is limited to appointment types explicitly enabled by the practice.
- Available time slots are displayed based on provider availability rules.
- The patient receives immediate confirmation and calendar integration (ICS file, Google Calendar, Apple Calendar).
- Self-service cancellations are subject to a configurable cancellation policy (e.g., 24-hour minimum notice).

#### US-SC-004: Resource Management

**As a** administrative staff member, **I want to** manage rooms, equipment, and provider schedules **so that** scheduling conflicts are avoided and resources are optimized.

**Acceptance Criteria:**
- Resources (rooms, equipment) are defined with availability windows and capacity.
- Appointment types can require specific resources (e.g., a procedure requires the procedure room).
- The system detects and prevents resource conflicts.
- Resource utilization reports are available.

#### US-SC-005: Waitlist Management

**As a** administrative staff member, **I want to** maintain a waitlist of patients seeking earlier appointments **so that** cancelled slots can be filled quickly.

**Acceptance Criteria:**
- Patients can be added to the waitlist with preferred date/time ranges and providers.
- When a matching slot becomes available, the system notifies waitlisted patients in priority order.
- Patients can accept or decline the offered slot via SMS or portal.
- If declined or not responded to within a configurable window, the next patient on the list is notified.

#### US-SC-006: Appointment Reminders

**As a** administrative staff member, **I want to** send automated appointment reminders **so that** no-show rates are reduced.

**Acceptance Criteria:**
- Reminders are sent via SMS, email, and/or portal notification based on patient preference.
- Default reminder schedule: 7 days, 2 days, and 2 hours before the appointment.
- Reminder schedules are configurable per appointment type.
- Patients can confirm or request rescheduling directly from the reminder.
- Reminder delivery status is tracked and visible to staff.

---

### Epic 6: Clinical Decision Support (CDS)

#### US-CDS-001: Drug Interaction Alerts

**As a** physician, **I want to** receive real-time alerts for clinically significant drug interactions **so that** I can make safer prescribing decisions.

**Acceptance Criteria:**
- Alerts fire during medication order entry and medication reconciliation.
- Alert severity is classified (contraindicated, serious, moderate, minor).
- Contraindicated alerts are hard stops requiring documented override justification.
- The system supports organizational customization of alert thresholds to reduce alert fatigue.
- Alert override rates are tracked for quality improvement reporting.

#### US-CDS-002: Preventive Care Reminders

**As a** physician, **I want to** see preventive care recommendations based on the patient's age, sex, and risk factors **so that** I do not miss recommended screenings and vaccinations.

**Acceptance Criteria:**
- Recommendations are based on USPSTF guidelines, ACIP immunization schedules, and configurable organizational protocols.
- Reminders are displayed on the patient chart dashboard and during encounters.
- Completed items are automatically cleared when corresponding documentation or results are recorded.
- Overdue items are highlighted with aging indicators.

#### US-CDS-003: Clinical Guidelines

**As a** physician, **I want to** access evidence-based clinical guidelines within the EHR workflow **so that** I can reference best practices during patient encounters.

**Acceptance Criteria:**
- Guidelines are available as InfoButton links (HL7 Infobutton standard) contextually triggered by diagnosis, medication, or lab result.
- Local clinical pathways can be authored and associated with diagnosis codes.
- Guideline content is accessible within two clicks from any relevant context in the chart.

#### US-CDS-004: Sepsis Screening Alert

**As a** nurse, **I want to** receive an automated sepsis screening alert when a patient meets SIRS criteria **so that** early intervention can be initiated.

**Acceptance Criteria:**
- The alert evaluates documented vital signs and lab results against SIRS/qSOFA criteria in real time.
- The alert fires within 60 seconds of the triggering data point being entered.
- The alert includes the specific criteria met and recommended next steps.
- Acknowledgment and response actions are documented and auditable.

#### US-CDS-005: Duplicate Order Detection

**As a** physician, **I want to** be warned when I order a test that was recently ordered or has recent results **so that** unnecessary duplicate testing is avoided.

**Acceptance Criteria:**
- Duplicate detection checks against orders placed within a configurable lookback window (default: 7 days for labs, 30 days for imaging).
- The alert displays the previous order date, status, and results (if available).
- The physician can proceed with the duplicate order by providing a clinical justification.

---

### Epic 7: Results Management

#### US-RM-001: Lab Result Review

**As a** physician, **I want to** review laboratory results in a clear, organized format **so that** I can make timely clinical decisions.

**Acceptance Criteria:**
- Results are displayed in a tabular format with abnormal values highlighted (high in red, low in blue, critical in bold red).
- Results include reference ranges, units, and performing laboratory.
- Trending is available for repeated tests, with a graphical view option.
- Results are filterable by date range, test category, and normal/abnormal status.
- Results are persisted as FHIR Observation and DiagnosticReport resources.

#### US-RM-002: Critical Value Notification

**As a** physician, **I want to** receive immediate notification of critical laboratory or imaging results **so that** I can take urgent action.

**Acceptance Criteria:**
- Critical values trigger a real-time notification (in-app alert, SMS, and/or page) to the ordering provider.
- If the ordering provider does not acknowledge within a configurable window (default: 30 minutes), the notification escalates to a covering provider.
- Acknowledgment includes: time, provider name, and intended action.
- The entire notification and acknowledgment chain is logged for compliance.

#### US-RM-003: Result Routing and Assignment

**As a** physician, **I want to** route results to other providers for review or action **so that** results are addressed even when I am unavailable.

**Acceptance Criteria:**
- Results can be forwarded to another provider with a free-text message.
- Coverage rules automatically route results to the on-call provider when the ordering provider is out.
- Unreviewed results are displayed in an inbox with aging indicators.
- A result is not considered "reviewed" until a provider explicitly marks it as such.

#### US-RM-004: Imaging Result Review

**As a** physician, **I want to** view imaging study reports and images within the EHR **so that** I do not need to switch to a separate application.

**Acceptance Criteria:**
- Radiology reports are displayed as structured text with impression highlighted.
- A DICOM image viewer is available for direct image viewing (basic windowing, zoom, pan, measure).
- Integration with external PACS via DICOMweb or IHE profiles is supported.
- Results are persisted as FHIR DiagnosticReport and ImagingStudy resources.

#### US-RM-005: Patient Result Notification

**As a** patient, **I want to** receive notification when my test results are available **so that** I can review them promptly.

**Acceptance Criteria:**
- Patients are notified via their preferred channel (portal, email, SMS) when results are released.
- Providers can hold results for a configurable period (default: 72 hours) before automatic patient release, in accordance with the 21st Century Cures Act information blocking rules.
- Normal results include patient-friendly explanations.
- Abnormal results include a recommendation to contact the provider.

---

### Epic 8: Patient Portal

#### US-PP-001: Health Record Access

**As a** patient, **I want to** view my health records (medications, allergies, conditions, immunizations, lab results) **so that** I can stay informed about my health.

**Acceptance Criteria:**
- Records are displayed in patient-friendly language with medical terminology explanations.
- Data availability complies with the 21st Century Cures Act (no information blocking).
- Records are exportable as C-CDA documents and FHIR resources.
- The portal supports USCDI v3 data elements.

#### US-PP-002: Secure Messaging

**As a** patient, **I want to** send secure messages to my care team **so that** I can ask non-urgent questions without scheduling an appointment.

**Acceptance Criteria:**
- Messages are encrypted in transit and at rest.
- File attachments (images, PDFs) are supported with size limits (10 MB per attachment).
- Messages are routed to the patient's care team inbox (not directly to a single provider).
- Auto-reply acknowledges receipt and sets response time expectations (e.g., 2 business days).
- Messages are persisted as FHIR Communication resources.

#### US-PP-003: Online Appointment Management

**As a** patient, **I want to** request, schedule, reschedule, and cancel appointments online **so that** I can manage my care on my own schedule.

**Acceptance Criteria:**
- See US-SC-003 acceptance criteria.
- Additionally, the portal displays upcoming and past appointments with visit summaries.

#### US-PP-004: Pre-Visit Questionnaires

**As a** patient, **I want to** complete pre-visit questionnaires before my appointment **so that** my provider has relevant information and the visit is more efficient.

**Acceptance Criteria:**
- Questionnaires are assigned based on appointment type and due date.
- Questionnaires are mobile-friendly and accessible (WCAG 2.1 AA).
- Completed questionnaires are available to the clinician in the encounter workflow.
- Questionnaires are persisted as FHIR QuestionnaireResponse resources.

#### US-PP-005: Proxy Access

**As a** patient (parent/guardian), **I want to** access my minor child's health records through the portal **so that** I can manage their healthcare.

**Acceptance Criteria:**
- Proxy access is configurable by relationship type and patient age.
- Adolescent privacy rules (state-specific) are enforced, restricting proxy access to sensitive encounters.
- Proxy access is logged separately from direct patient access.
- Proxy relationships are managed as FHIR RelatedPerson resources.

#### US-PP-006: Bill Viewing and Payment

**As a** patient, **I want to** view my account balance and make payments online **so that** I can manage my financial obligations conveniently.

**Acceptance Criteria:**
- Outstanding balances, statement history, and payment history are displayed.
- Online payment is supported via credit card, debit card, and ACH.
- Payment processing is PCI DSS compliant.
- Payment plans can be set up for balances above a configurable threshold.

---

### Epic 9: Reporting and Analytics

#### US-RA-001: Quality Measure Reporting

**As a** compliance officer, **I want to** generate CMS quality measure reports (eCQM) **so that** the organization can meet MIPS/APM reporting requirements.

**Acceptance Criteria:**
- The system calculates eCQMs using CQL (Clinical Quality Language) measure definitions.
- Reports are exportable in QRDA Category I (individual) and Category III (aggregate) formats.
- A dashboard displays current performance against each measure with numerator/denominator detail.
- Historical trending of quality measure performance is available.

#### US-RA-002: Operational Dashboards

**As a** administrative staff member, **I want to** view operational dashboards (appointment volumes, no-show rates, provider utilization) **so that** I can optimize clinic operations.

**Acceptance Criteria:**
- Dashboards are pre-built for common metrics and customizable.
- Data refreshes at configurable intervals (minimum: every 15 minutes).
- Dashboards support drill-down from summary to detail level.
- Dashboard access is controlled by role-based permissions.

#### US-RA-003: Population Health Analytics

**As a** physician, **I want to** identify and manage patient populations (e.g., all diabetics with HbA1c > 9%) **so that** I can proactively manage chronic conditions.

**Acceptance Criteria:**
- Population queries support filtering by diagnosis, lab value, medication, age, sex, race, ethnicity, and payer.
- Results can be exported as patient lists for outreach campaigns.
- Risk stratification is available based on validated models (e.g., HCC, Charlson Comorbidity Index).
- Panel management views show care gap status for each patient.

#### US-RA-004: Ad Hoc Reporting

**As a** system administrator, **I want to** create ad hoc reports using a visual report builder **so that** I can answer operational and clinical questions without custom development.

**Acceptance Criteria:**
- A drag-and-drop report builder supports selecting data fields, filters, groupings, and visualizations.
- Reports can query de-identified data only, unless the user has a PHI access role.
- Reports can be scheduled and distributed via email as PDF or CSV.
- Saved reports are shareable with other authorized users.

---

### Epic 10: Security and Access Control

#### US-SA-001: Role-Based Access Control (RBAC)

**As a** system administrator, **I want to** define roles with granular permissions **so that** users only access the functions and data they need for their job.

**Acceptance Criteria:**
- The system ships with default roles: Physician, Nurse, Medical Assistant, Front Desk, Billing, System Admin, Compliance Officer, and Patient.
- Custom roles can be created with any combination of permissions.
- Permissions are granular (e.g., `patient.demographics.read`, `patient.demographics.write`, `note.sign`, `order.medication.write`).
- Role assignments are effective immediately upon save.
- Role changes are logged in the audit trail.

#### US-SA-002: Multi-Factor Authentication (MFA)

**As a** system administrator, **I want to** enforce multi-factor authentication for all clinical users **so that** compromised credentials alone cannot grant access to PHI.

**Acceptance Criteria:**
- MFA is enforced for all users by default; it can be required per role.
- Supported MFA methods: TOTP (authenticator app), FIDO2/WebAuthn (hardware key), and push notifications via authenticator apps. SMS is explicitly excluded as an MFA factor per NIST SP 800-63B guidance due to known vulnerabilities in SMS delivery (SIM-swap, SS7 interception).
- MFA is required at initial login and optionally at session resumption after idle timeout.
- EPCS workflows require FIPS 140-2 validated MFA.

#### US-SA-003: Comprehensive Audit Trail

**As a** compliance officer, **I want to** review a complete audit trail of all system access and data modifications **so that** I can investigate potential breaches and demonstrate compliance.

**Acceptance Criteria:**
- Every access event is logged: login/logout, patient record access (view, create, update, delete), order actions, report generation, and export operations.
- Audit log entries include: timestamp (UTC), user ID, user role, action type, resource accessed (including patient MRN), source IP, user agent, and outcome (success/failure).
- Audit logs are immutable (append-only) and tamper-evident (hash-chained).
- Audit logs are retained for a minimum of 7 years (configurable).
- Audit log search supports filtering by user, patient, date range, and action type with results returned within 5 seconds.
- Audit data is persisted as FHIR AuditEvent resources.

#### US-SA-004: Break-the-Glass Access

**As a** physician, **I want to** access a patient's record in an emergency even when I do not have a pre-existing treatment relationship **so that** I can provide emergency care.

**Acceptance Criteria:**
- Break-the-glass is available only when normal access is denied.
- The user must provide a reason (selected from a predefined list: emergency care, on-call coverage, public health, etc.) before access is granted.
- Break-the-glass access is time-limited (default: 60 minutes; configurable maximum of 4 hours requiring security officer approval).
- Periodic re-authentication is required every 30 minutes during an active break-the-glass session.
- The access event is flagged in the audit log and immediately reported to the compliance team.
- Reporting provides: user identity, patient accessed, reason given, and duration of access.

#### US-SA-005: Session Management

**As a** system administrator, **I want to** enforce session timeout and concurrent session policies **so that** unattended workstations do not expose PHI.

**Acceptance Criteria:**
- Idle session timeout is configurable (default: 15 minutes).
- Screen lock activates before session termination, requiring re-authentication.
- Concurrent session limits are enforceable per role.
- Active sessions can be viewed and terminated by administrators.

#### US-SA-006: Data Encryption

**As a** system administrator, **I want to** ensure all PHI is encrypted at rest and in transit **so that** data is protected even if storage media or network traffic is compromised.

**Acceptance Criteria:**
- Data at rest is encrypted using AES-256 via AWS KMS with customer-managed keys.
- Data in transit is encrypted using TLS 1.2 or higher.
- Database field-level encryption is applied to highly sensitive fields (SSN, substance abuse notes).
- Encryption key rotation occurs automatically on a configurable schedule (default: annual).

---

### Epic 11: Interoperability

#### US-INT-001: FHIR R4 API

**As a** system administrator, **I want to** expose a FHIR R4 REST API **so that** third-party applications and health information exchanges can access and exchange data.

**Acceptance Criteria:**
- The API implements US Core Implementation Guide (v5.0+) profiles.
- All USCDI v3 data elements are supported.
- The API supports CRUD operations, search parameters, and includes/revincludes as defined in US Core.
- SMART on FHIR authorization (OAuth 2.0 + OpenID Connect) is enforced for all API access.
- The API serves a FHIR CapabilityStatement at the `/metadata` endpoint.
- Rate limiting is configurable per client application.

#### US-INT-002: SMART on FHIR App Launch

**As a** physician, **I want to** launch third-party SMART on FHIR applications from within the EHR **so that** I can use specialized tools without leaving the clinical workflow.

**Acceptance Criteria:**
- The system supports the SMART App Launch Framework (v2.0) for EHR launch and standalone launch.
- Application registration includes: name, redirect URIs, requested scopes, and organizational approval status.
- Launch context provides patient, encounter, and user information.
- Application access is controlled by organizational policy (allowlist).

#### US-INT-003: HL7v2 Interfaces

**As a** system administrator, **I want to** send and receive HL7v2 messages **so that** the system can integrate with legacy laboratory, radiology, and hospital systems.

**Acceptance Criteria:**
- Supported message types: ADT (A01, A02, A03, A04, A08), ORM/OML (O01, O21), ORU (R01), SIU (S12, S13, S14, S15), MDM (T02).
- The system acts as both sender and receiver via MLLP/TLS.
- Interface configurations are manageable through an admin UI (endpoint, port, message mapping).
- Message queuing with retry logic ensures delivery reliability.
- Failed messages are quarantined with error details for manual resolution.

#### US-INT-004: C-CDA Document Exchange

**As a** physician, **I want to** send and receive C-CDA documents (Continuity of Care Documents, Discharge Summaries) **so that** patient records are shared during transitions of care.

**Acceptance Criteria:**
- The system generates valid C-CDA R2.1 documents conforming to the following templates: CCD, Referral Note, Discharge Summary, Progress Note.
- Inbound C-CDA documents are parsed and presented to clinicians for reconciliation.
- Reconciled data is imported into the appropriate FHIR resources.
- Document exchange is supported via Direct messaging (HISP integration).

#### US-INT-005: Bulk Data Export

**As a** system administrator, **I want to** perform FHIR Bulk Data Access exports **so that** population-level data can be extracted for analytics, public health reporting, and research.

**Acceptance Criteria:**
- The system implements the FHIR Bulk Data Access IG (v2.0).
- Export supports: System-level, Group-level, and Patient-level export.
- Output format is NDJSON.
- Export jobs are asynchronous with status polling.
- Access is restricted to authorized backend service applications using the SMART Backend Services authorization profile.

#### US-INT-006: Health Information Exchange (HIE) Connectivity

**As a** system administrator, **I want to** connect to regional and national Health Information Exchanges **so that** patient records are available across care settings.

**Acceptance Criteria:**
- The system supports IHE profiles: XDS.b, XCA, XDR, PDQ, PIX.
- Patient discovery queries can be initiated from within the chart.
- Retrieved documents are displayable and reconcilable within the EHR.
- Consent management supports opt-in and opt-out models per state regulations.

---

### Epic 12: Vital Signs Documentation

#### US-VS-001: Vital Signs Entry

**As a** nurse, **I want to** document a patient's vital signs during intake and throughout the encounter **so that** clinicians have current physiological measurements for clinical decision-making.

**Acceptance Criteria:**
- The vital signs form captures: height, weight, BMI (auto-calculated from height and weight), blood pressure (systolic and diastolic), heart rate, respiratory rate, temperature, pulse oximetry (SpO2), and pain score (0--10 scale).
- BMI is automatically calculated and displayed when both height and weight are entered.
- All vital signs are recorded with the measurement date/time and the documenting user.
- Vital signs outside configurable normal ranges are flagged with visual indicators (color coding and icons).
- Vital signs are persisted as FHIR Observation resources per USCDI v3 data classes.
- Vital signs entry supports both metric and imperial units with automatic conversion.

#### US-VS-002: Vital Signs Trending

**As a** physician, **I want to** view vital signs trends over time with configurable date ranges and abnormal value alerts **so that** I can identify clinically significant changes in the patient's condition.

**Acceptance Criteria:**
- Vital signs are displayed in both tabular and graphical (trend line) formats.
- Date ranges are configurable (last visit, 30 days, 90 days, 1 year, all).
- Normal ranges are configurable per patient age, sex, and clinical context.
- Values outside normal ranges are highlighted in both tabular and graphical views.
- Trend charts support overlay of multiple vital sign types for correlation analysis.
- Trending data is available within the encounter workflow and as a standalone chart section.

---

### Epic 13: Encounter Management

#### US-ENC-001: Encounter Creation and Management

**As a** clinician, **I want to** create and manage patient encounters/visits **so that** clinical activities are organized within the context of a specific patient interaction.

**Acceptance Criteria:**
- Encounters are created with: patient, encounter type (office visit, telehealth, phone, etc.), date/time, participating providers, location, and chief complaint.
- Encounter status follows a defined workflow: planned -> arrived -> in-progress -> finished -> cancelled.
- Status transitions are validated (e.g., cannot transition from cancelled to in-progress).
- Encounters are linked to the originating appointment (if applicable).
- Encounters are persisted as FHIR Encounter resources.

#### US-ENC-002: Encounter Documentation

**As a** clinician, **I want to** associate clinical documentation (chief complaint, diagnoses, procedures, orders, and notes) with a specific encounter **so that** all clinical activities for a visit are traceable and organized.

**Acceptance Criteria:**
- Chief complaint and encounter type are captured at encounter creation or check-in.
- Diagnoses (FHIR Condition), procedures (FHIR Procedure), observations (FHIR Observation), orders (FHIR MedicationRequest, ServiceRequest), and notes (FHIR DocumentReference) can be associated with the encounter.
- The encounter summary view displays all associated clinical data in a consolidated timeline.
- Encounter diagnoses are distinguishable from problem list conditions.

---

### Epic 14: Immunization Management

#### US-IMM-001: Immunization Recording

**As a** nurse, **I want to** record administered immunizations with complete administration details **so that** the patient's immunization record is accurate and reportable.

**Acceptance Criteria:**
- Immunization records capture: vaccine code (CVX), manufacturer (MVX), lot number, expiration date, administration site, route, dose quantity, administering provider, and date administered.
- Vaccine Inventory System (VIS) date and edition are recorded.
- Contraindications and refusals are documented with reason codes.
- Administered immunizations are reported to state immunization registries via HL7v2 VXU^V04.
- Immunization records are persisted as FHIR Immunization resources.

#### US-IMM-002: Immunization History and Forecasting

**As a** physician, **I want to** view a patient's immunization history and see recommended/overdue vaccines **so that** I can ensure the patient is up to date on recommended immunizations.

**Acceptance Criteria:**
- Immunization history displays all recorded and externally sourced (registry query) immunizations in chronological order.
- Immunization forecasts are generated based on the CDC immunization schedule (ACIP recommendations), patient age, and prior immunization history.
- Overdue immunizations are highlighted with aging indicators.
- Forecasting accounts for catch-up schedules and contraindications.
- The immunization record is printable for school/employer requirements.

---

### Epic 15: User and Role Management

#### US-UM-001: User Account Management

**As a** system administrator, **I want to** create, update, and deactivate user accounts with appropriate role assignments **so that** users have the access they need and former users are promptly deprovisioned.

**Acceptance Criteria:**
- User accounts are created with: name, email, role(s), department, credential type, NPI (if applicable), and supervisor.
- Role assignment follows the principle of least privilege; users are assigned only the roles necessary for their job function.
- Account deactivation immediately revokes all active sessions and prevents future login.
- User provisioning follows a workflow requiring manager approval before account activation.
- All user account changes are logged in the audit trail.

#### US-UM-002: Custom Role and Permission Management

**As a** system administrator, **I want to** define custom roles with granular permissions **so that** the access control model reflects the organization's unique workflow requirements.

**Acceptance Criteria:**
- Custom roles can be created with any combination of resource-level (e.g., patient, encounter, medication) and operation-level (e.g., read, write, delete, sign) permissions.
- Permissions are managed via a junction table model supporting many-to-many relationships between roles and permissions.
- Role changes take effect immediately for all users assigned to the modified role.
- A role comparison view shows the permission differences between any two roles.
- Default system roles cannot be deleted but can be cloned and customized.

#### US-UM-003: Quarterly Access Reviews

**As a** compliance officer, **I want to** conduct automated quarterly access reviews **so that** user access remains appropriate and excessive permissions are identified and remediated.

**Acceptance Criteria:**
- The system generates a quarterly access review report listing all users, their roles, and last login date.
- Users who have not logged in within 90 days are flagged for deactivation review.
- Department managers receive automated notifications to certify their team members' access.
- Uncertified accounts are automatically escalated to the security team after a configurable review period (default: 14 days).
- Access review completion status and results are retained for compliance audit purposes.

---

### Epic 16: Consent Management

#### US-CON-001: Consent Recording

**As a** administrative staff member, **I want to** record patient consent for treatment, data sharing, and research **so that** the organization has documented authorization for specific uses of the patient's health information.

**Acceptance Criteria:**
- Consent records capture: consent type (treatment, data sharing, research, marketing), scope (entire record, specific data categories, specific providers), effective period, and patient signature.
- Consent is recorded as a FHIR Consent resource with granular scope definitions.
- Electronic signature capture is supported with identity verification.
- Consent forms are configurable per organizational policy and regulatory requirements.

#### US-CON-002: Consent Enforcement

**As a** system administrator, **I want to** enforce consent decisions at the point of data access **so that** patient data is only shared in accordance with their documented consent.

**Acceptance Criteria:**
- The consent evaluation engine is integrated at the data access layer, evaluating consent status before returning data.
- Data access requests for patients without active consent for the requested purpose are denied with a clear indication to the requesting user.
- Consent enforcement applies to FHIR API access, C-CDA exports, bulk data exports, and inter-system data sharing.
- Override is available only via break-the-glass for emergency situations.

#### US-CON-003: Consent Withdrawal

**As a** patient, **I want to** withdraw my consent for data sharing with immediate effect **so that** my health information is no longer shared with parties I no longer authorize.

**Acceptance Criteria:**
- Consent withdrawal can be initiated via the patient portal or in-person with staff assistance.
- Withdrawal takes effect immediately upon confirmation; subsequent data access requests are denied for the withdrawn scope.
- Prior disclosures made under the original consent remain valid and are documented in the accounting of disclosures.
- The patient receives confirmation of the withdrawal with a summary of its scope and effect.

#### US-CON-004: 42 CFR Part 2 Consent Workflow (P1, Phase 2)

**As a** clinician, **I want to** manage consent for substance use disorder (SUD) treatment records in compliance with 42 CFR Part 2 **so that** SUD records receive the enhanced protections required by federal law.

**Acceptance Criteria:**
- The 42 CFR Part 2 consent form includes all required elements per 42 CFR 2.31: name of patient, specific purpose of disclosure, how much and what kind of information to be disclosed, name of recipient, patient signature, date, and right to revoke.
- Part 2 consent is managed separately from general treatment consent.
- Re-disclosure prohibition notices are automatically appended to any output (printed, exported, transmitted) containing Part 2 protected data.
- Part 2 data is segmented and access-controlled independently from standard clinical data.
- Consent expiration is tracked with automated notifications for renewal.

---

### Epic 17: Psychotherapy Notes Protection (P1, Phase 2)

#### US-PSY-001: Psychotherapy Notes Classification

**As a** compliance officer, **I want to** ensure psychotherapy notes are classified and stored as a distinct data category per HIPAA 164.508(a)(2) **so that** they receive enhanced protections separate from standard clinical documentation.

**Acceptance Criteria:**
- Psychotherapy notes are classified as a distinct data type, separate from standard clinical progress notes.
- Psychotherapy notes are stored in a separate, access-controlled data store (or logical partition) from standard clinical notes.
- Authorization for psychotherapy notes requires a specific, patient-signed authorization per HIPAA 164.508(a)(2); standard TPO (Treatment, Payment, Operations) consent does not grant access.
- Psychotherapy notes are excluded from standard record disclosures, patient portal access, C-CDA exports, FHIR bulk data exports, and responses to subpoenas unless accompanied by specific authorization or court order.
- Access to psychotherapy notes is restricted to the authoring clinician and explicitly authorized individuals.
- All access to psychotherapy notes is logged as a distinct audit event category.

---

## 5. Functional Requirements

Requirements are identified with a unique ID (FR-XXX), grouped by module, and prioritized:

| Priority | Definition |
|----------|------------|
| **P0** | Must have for MVP (Phase 1); system is non-functional without it |
| **P1** | Must have for Phase 2; critical for certification and core workflows |
| **P2** | Should have for Phase 3; differentiating feature |
| **P3** | Nice to have; planned for future consideration |

### 5.1 Patient Management

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-001 | The system shall allow creation of patient records with demographics compliant with USCDI v3. | P0 | US-PM-001 |
| FR-002 | The system shall generate a unique MRN for each patient upon registration. | P0 | US-PM-001 |
| FR-003 | The system shall perform automatic duplicate detection during patient creation using probabilistic patient matching with a weighted scoring algorithm and configurable thresholds. Minimum match fields: last name, first name, date of birth, SSN (exact match via HMAC). Match score >= 0.85 = auto-link; 0.65--0.85 = manual review; < 0.65 = new record. False positive rate target: < 1%. | P0 | US-PM-001 |
| FR-004 | The system shall support patient search by name (partial, phonetic), DOB, MRN, SSN, and phone number with results returned in under 500ms. | P0 | US-PM-002 |
| FR-005 | The system shall maintain a versioned history of all demographic changes with user attribution. | P0 | US-PM-003 |
| FR-006 | The system shall support primary, secondary, and tertiary insurance coverage records per patient. | P0 | US-PM-004 |
| FR-007 | The system shall perform real-time insurance eligibility verification via X12 270/271. | P1 | US-PM-004 |
| FR-008 | The system shall support merging of duplicate patient records with full data consolidation and reversibility. | P1 | US-PM-005 |
| FR-009 | The system shall support patient photograph capture and storage. | P2 | US-PM-006 |
| FR-010 | The system shall store all patient data as FHIR R4 Patient resources. | P0 | US-PM-001 |

### 5.2 Clinical Documentation

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-011 | The system shall provide a SOAP note editor with discrete sections and rich text editing. | P0 | US-CD-001 |
| FR-012 | The system shall auto-save clinical notes every 30 seconds and on section blur. | P0 | US-CD-001 |
| FR-013 | The system shall support ICD-10-CM code lookup with typeahead search in the Assessment section. | P0 | US-CD-001 |
| FR-014 | The system shall support inline order entry within the Plan section of a note. | P0 | US-CD-001 |
| FR-015 | The system shall provide pre-built documentation templates for common visit types. | P0 | US-CD-002 |
| FR-016 | The system shall support creation and management of custom documentation templates with smart macros and conditional logic. | P1 | US-CD-002 |
| FR-017 | The system shall enforce two-factor re-authentication for note signing. | P0 | US-CD-003 |
| FR-018 | The system shall lock signed notes and support addendum and amendment workflows. | P0 | US-CD-003, US-CD-004 |
| FR-019 | The system shall record note signing as a FHIR Provenance resource. | P0 | US-CD-003 |
| FR-020 | The system shall support co-signature workflows for supervised clinicians. | P1 | US-CD-003 |
| FR-021 | The system shall integrate with HIPAA-compliant speech-to-text for voice dictation. | P2 | US-CD-005 |
| FR-022 | The system shall maintain a coded problem list with ICD-10/SNOMED CT and status tracking. | P0 | US-CD-006 |
| FR-023 | The system shall maintain a coded allergy list with RxNorm/SNOMED CT, reaction type, and severity. | P0 | US-CD-007 |
| FR-024 | The system shall persist clinical documents as FHIR DocumentReference and Composition resources. | P0 | US-CD-001 |

### 5.3 Order Entry / CPOE

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-025 | The system shall support medication order entry with RxNorm-coded drug selection, dosing, route, frequency, and pharmacy selection. | P0 | US-OE-001 |
| FR-026 | The system shall perform real-time drug-drug, drug-allergy, and drug-condition interaction checking during medication ordering. | P0 | US-OE-001 |
| FR-027 | The system shall support laboratory order entry with LOINC-coded test selection. | P0 | US-OE-002 |
| FR-028 | The system shall support imaging order entry with CPT/RADLEX-coded study selection. | P1 | US-OE-003 |
| FR-029 | The system shall perform Appropriate Use Criteria consultation for advanced imaging orders. | P1 | US-OE-003 |
| FR-030 | The system shall support referral order entry with specialist network lookup and clinical context sharing. | P1 | US-OE-004 |
| FR-031 | The system shall support configurable order sets with conditional logic. | P1 | US-OE-005 |
| FR-032 | The system shall perform duplicate order detection with configurable lookback windows. | P1 | US-CDS-005 |
| FR-033 | The system shall persist all orders as FHIR MedicationRequest or ServiceRequest resources. | P0 | US-OE-001, US-OE-002, US-OE-003 |

### 5.4 Medication Management

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-034 | The system shall transmit prescriptions electronically via NCPDP SCRIPT 2017071. | P1 | US-MM-001 |
| FR-035 | The system shall support EPCS with DEA-compliant two-factor authentication. | P1 | US-MM-001 |
| FR-036 | The system shall receive and display pharmacy fill/refill notifications (RxFill). | P1 | US-MM-001 |
| FR-037 | The system shall perform real-time formulary checking via NCPDP RTPB and display patient cost estimates. | P2 | US-MM-003 |
| FR-038 | The system shall support medication reconciliation workflows with external pharmacy data integration. | P1 | US-MM-004 |
| FR-039 | The system shall provide a medication administration record (MAR) with barcode verification. | P1 | US-MM-005 |
| FR-040 | The system shall maintain a complete medication history with statuses (active, discontinued, completed, on hold). | P0 | US-MM-004 |

### 5.5 Scheduling

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-041 | The system shall support appointment scheduling with configurable provider availability templates. | P0 | US-SC-001 |
| FR-042 | The system shall prevent double-booking unless explicitly permitted by schedule configuration. | P0 | US-SC-001 |
| FR-043 | The system shall send automated appointment confirmations and reminders via SMS, email, and portal. | P0 | US-SC-006 |
| FR-044 | The system shall support appointment rescheduling and cancellation with reason tracking. | P0 | US-SC-002 |
| FR-045 | The system shall support patient self-scheduling via the patient portal for designated appointment types. | P1 | US-SC-003 |
| FR-046 | The system shall manage resources (rooms, equipment) with conflict detection. | P1 | US-SC-004 |
| FR-047 | The system shall maintain a waitlist with automated notification when matching slots become available. | P2 | US-SC-005 |
| FR-048 | The system shall persist appointments as FHIR Appointment and Schedule resources. | P0 | US-SC-001 |

### 5.6 Clinical Decision Support

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-049 | The system shall provide configurable drug interaction alerts with severity classification and override documentation. | P0 | US-CDS-001 |
| FR-050 | The system shall display preventive care reminders based on USPSTF and ACIP guidelines. | P1 | US-CDS-002 |
| FR-051 | The system shall provide contextual clinical guideline links via HL7 Infobutton. | P2 | US-CDS-003 |
| FR-052 | The system shall support configurable clinical alert rules (e.g., sepsis screening, VTE prophylaxis). | P1 | US-CDS-004 |
| FR-053 | The system shall track alert override rates for quality improvement. | P1 | US-CDS-001 |
| FR-054 | The system shall support CDS Hooks for external decision support integration. | P2 | US-CDS-003 |

### 5.7 Results Management

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-055 | The system shall display lab results with abnormal value highlighting, reference ranges, and graphical trending. | P1 | US-RM-001 |
| FR-056 | The system shall provide real-time critical value notifications with escalation and acknowledgment tracking. | P1 | US-RM-002 |
| FR-057 | The system shall support result routing, forwarding, and coverage-based auto-routing. | P1 | US-RM-003 |
| FR-058 | The system shall maintain a provider inbox for unreviewed results with aging indicators. | P1 | US-RM-003 |
| FR-059 | The system shall display imaging reports and provide a basic DICOM image viewer or PACS integration. | P1 | US-RM-004 |
| FR-060 | The system shall notify patients when results are available, with configurable hold periods. | P1 | US-RM-005 |
| FR-061 | The system shall persist results as FHIR Observation and DiagnosticReport resources. | P1 | US-RM-001 |

### 5.8 Patient Portal

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-062 | The system shall provide a patient-facing portal for health record access compliant with the 21st Century Cures Act. | P1 | US-PP-001 |
| FR-063 | The system shall support secure messaging between patients and care teams. | P1 | US-PP-002 |
| FR-064 | The system shall support patient self-scheduling for designated appointment types. | P1 | US-PP-003 |
| FR-065 | The system shall support configurable pre-visit questionnaires with mobile-friendly forms. | P1 | US-PP-004 |
| FR-066 | The system shall support proxy access with adolescent privacy protections. | P2 | US-PP-005 |
| FR-067 | The system shall support online bill viewing and payment processing (PCI DSS compliant). | P2 | US-PP-006 |
| FR-068 | The system shall export patient records as C-CDA documents and FHIR resources on patient request. | P1 | US-PP-001 |

### 5.9 Reporting and Analytics

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-069 | The system shall calculate and report electronic Clinical Quality Measures (eCQM) using CQL. | P1 | US-RA-001 |
| FR-070 | The system shall export quality reports in QRDA Category I and Category III formats. | P1 | US-RA-001 |
| FR-071 | The system shall provide pre-built operational dashboards with drill-down capability. | P2 | US-RA-002 |
| FR-072 | The system shall support population health queries with risk stratification. | P2 | US-RA-003 |
| FR-073 | The system shall provide an ad hoc report builder with visual query construction. | P2 | US-RA-004 |
| FR-074 | The system shall support scheduled report generation and distribution. | P2 | US-RA-004 |

### 5.10 Security and Access Control

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-075 | The system shall enforce role-based access control with granular, configurable permissions. | P0 | US-SA-001 |
| FR-076 | The system shall enforce multi-factor authentication for all users with FIPS 140-2 validated methods for EPCS. | P0 | US-SA-002 |
| FR-077 | The system shall maintain a comprehensive, immutable, tamper-evident audit trail of all access and data modifications. | P0 | US-SA-003 |
| FR-078 | The system shall support break-the-glass emergency access with reason documentation and compliance notification. | P0 | US-SA-004 |
| FR-079 | The system shall enforce configurable session timeout and support concurrent session limits. | P0 | US-SA-005 |
| FR-080 | The system shall encrypt all PHI at rest (AES-256) and in transit (TLS 1.2+). | P0 | US-SA-006 |
| FR-081 | The system shall support automatic encryption key rotation. | P0 | US-SA-006 |
| FR-082 | The system shall retain audit logs for a minimum of 7 years. | P0 | US-SA-003 |

### 5.11 Interoperability

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-083 | The system shall expose a FHIR R4 REST API implementing US Core IG v5.0+ profiles. | P0 | US-INT-001 |
| FR-084 | The system shall enforce SMART on FHIR authorization (OAuth 2.0 + OIDC) for all API access. | P0 | US-INT-001 |
| FR-085 | The system shall support SMART App Launch Framework v2.0 for EHR and standalone launch. | P1 | US-INT-002 |
| FR-086 | The system shall send and receive HL7v2 messages (ADT, ORM, ORU, SIU, MDM) via MLLP/TLS. | P1 | US-INT-003 |
| FR-087 | The system shall generate and consume C-CDA R2.1 documents (CCD, Referral Note, Discharge Summary). | P1 | US-INT-004 |
| FR-088 | The system shall support FHIR Bulk Data Access for system-level and group-level export. | P1 | US-INT-005 |
| FR-089 | The system shall support Direct messaging for secure document exchange. | P1 | US-INT-004 |
| FR-090 | The system shall support IHE integration profiles (XDS.b, XCA, PDQ, PIX) for HIE connectivity. | P2 | US-INT-006 |
| FR-091 | The system shall publish a FHIR CapabilityStatement at the `/metadata` endpoint. | P0 | US-INT-001 |

### 5.12 Vital Signs Documentation

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-VS-001 | The system shall record and display vital signs (height, weight, BMI, blood pressure, heart rate, respiratory rate, temperature, pulse oximetry, pain score) per USCDI v3 data classes, persisted as FHIR Observation resources. | P0 | US-VS-001 |
| FR-VS-002 | The system shall auto-calculate BMI from height and weight entries and display the result immediately. | P0 | US-VS-001 |
| FR-VS-003 | The system shall flag vital signs outside configurable normal ranges (based on patient age, sex, and clinical context) with visual indicators and optional CDS alerts. | P0 | US-VS-001, US-VS-002 |

### 5.13 Encounter Management

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-ENC-001 | The system shall support creation, reading, and updating of encounters with a status workflow (planned -> arrived -> in-progress -> finished -> cancelled) and validated status transitions. | P0 | US-ENC-001 |
| FR-ENC-002 | The system shall associate observations, conditions, medication requests, service requests, procedures, and clinical notes with encounters via FHIR resource references. | P0 | US-ENC-002 |

### 5.14 Immunization Management

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-IMM-001 | The system shall support CRUD operations for immunization records per CVX (vaccine administered) and MVX (vaccine manufacturer) code sets, persisted as FHIR Immunization resources. | P1 | US-IMM-001 |
| FR-IMM-002 | The system shall generate immunization forecasts based on the CDC immunization schedule (ACIP recommendations), accounting for patient age, prior immunization history, catch-up schedules, and documented contraindications. | P1 | US-IMM-002 |

### 5.15 User and Role Management

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-UM-001 | The system shall support user CRUD operations with role assignment via junction tables, supporting many-to-many relationships between users and roles. | P0 | US-UM-001 |
| FR-UM-002 | The system shall implement a permission model supporting resource-level (e.g., patient, encounter, medication) and operation-level (e.g., read, write, delete, sign) grants. | P0 | US-UM-002 |
| FR-UM-003 | The system shall enforce a user provisioning workflow with manager approval before account activation. | P0 | US-UM-001 |

### 5.16 Consent Management

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-CON-001 | The system shall support FHIR Consent resources with granular scope definitions (consent type, data categories, authorized recipients, effective period). | P0 | US-CON-001 |
| FR-CON-002 | The system shall evaluate consent status at the data access layer, denying requests that lack active consent for the requested purpose and scope. | P0 | US-CON-002 |
| FR-CON-003 | The system shall support 42 CFR Part 2 consent workflows with all required elements per 42 CFR 2.31 (patient name, purpose of disclosure, information scope, recipient name, patient signature, date, right to revoke). | P1 | US-CON-004 |
| FR-CON-004 | The system shall automatically append re-disclosure prohibition notices to any output (printed, exported, transmitted) containing 42 CFR Part 2 protected data. | P1 | US-CON-004 |

### 5.17 Psychotherapy Notes Protection

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-PSY-001 | The system shall classify psychotherapy notes as a distinct data category per HIPAA 164.508(a)(2) with separate storage and authorization from standard clinical notes. | P1 | US-PSY-001 |
| FR-PSY-002 | The system shall exclude psychotherapy notes from standard TPO disclosures, patient portal access, C-CDA exports, FHIR bulk data exports, and general record requests unless accompanied by patient-specific authorization or court order. | P1 | US-PSY-001 |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-001 | Page load time (initial) | < 2 seconds (P95) | P0 |
| NFR-002 | Page load time (subsequent / SPA navigation) | < 500 milliseconds (P95) | P0 |
| NFR-003 | Patient search response time | < 500 milliseconds (P95) for up to 2M patient records | P0 |
| NFR-004 | FHIR API response time (single resource read) | < 200 milliseconds (P95) | P0 |
| NFR-005 | FHIR API response time (search with 100 results) | < 1 second (P95) | P0 |
| NFR-006 | Note auto-save latency | < 1 second (P99) | P0 |
| NFR-007 | Concurrent clinical users per tenant | 1,000 (Phase 1), 10,000 (Phase 2) | P0/P1 |
| NFR-008 | Order submission to acknowledgment | < 2 seconds (P95) | P0 |
| NFR-009 | Clinical decision support alert firing latency | < 3 seconds from trigger event | P1 |
| NFR-010 | Report generation (standard) | < 30 seconds for datasets up to 100K records | P1 |
| NFR-011 | Bulk data export throughput | 10,000 resources per minute minimum | P1 |

### 6.2 Scalability

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-012 | Horizontal scaling of API and application tiers | Auto-scaling based on CPU/memory/request-rate thresholds | P0 |
| NFR-013 | Database scaling | Read replicas for query workloads; write throughput supporting 5,000 transactions per second | P0 |
| NFR-014 | Multi-tenancy | The system supports multi-tenant deployment with schema-per-tenant data isolation in PostgreSQL. Each tenant has an isolated database schema. Cross-tenant data access is prevented at the database level. Tenant-specific encryption keys via AWS KMS. | P1 |
| NFR-015 | Storage scaling | Object storage for documents and images with no practical upper limit | P0 |
| NFR-016 | Message queue scaling | Auto-scaling consumers for HL7v2, FHIR subscriptions, and event processing | P1 |

### 6.3 Security

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-017 | Encryption at rest | AES-256 using AWS KMS with customer-managed CMKs | P0 |
| NFR-018 | Encryption in transit | TLS 1.2 minimum; TLS 1.3 preferred | P0 |
| NFR-019 | Authentication | SAML 2.0 and OpenID Connect federation; local credential store with Argon2id password hashing | P0 |
| NFR-020 | Authorization | OAuth 2.0 with SMART scopes; RBAC with attribute-based overrides | P0 |
| NFR-021 | Secret management | All secrets stored in AWS Secrets Manager; no secrets in code, config, or environment variables | P0 |
| NFR-022 | Vulnerability scanning | Automated SAST, DAST, and dependency scanning in CI/CD; critical/high findings block deployment | P0 |
| NFR-023 | Penetration testing | Annual third-party penetration test; remediation of critical findings within 30 days | P0 |
| NFR-024 | WAF and DDoS protection | AWS WAF and AWS Shield Standard at minimum | P0 |
| NFR-025 | Data loss prevention | PHI detection in logs and exports; automatic redaction | P0 |

### 6.4 Compliance

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-026 | HIPAA compliance | Full compliance with Privacy Rule, Security Rule, and Breach Notification Rule | P0 |
| NFR-027 | SOC 2 Type II | Achieve and maintain certification annually | P1 |
| NFR-028 | HITRUST CSF | Achieve r2 certification | P1 |
| NFR-029 | ONC Health IT Certification | 2015 Edition Cures Update certification for applicable criteria | P1 |
| NFR-030 | 21st Century Cures Act | Information blocking compliance; patient access API compliance | P0 |
| NFR-031 | State privacy laws | Configurable privacy rules for state-specific requirements (e.g., California CCPA, New York, Texas) | P1 |
| NFR-032 | 42 CFR Part 2 | Segmented access controls for substance use disorder treatment records | P1 |

### 6.5 Availability and Disaster Recovery

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-033 | Availability SLA | 99.9% uptime (measured monthly, excluding planned maintenance) | P0 |
| NFR-034 | Recovery Time Objective (RTO) | Tiered model: Tier 1 (Clinical Services) < 15 min; Tier 2 (Supporting Services) < 30 min; Tier 3 (Non-Clinical) < 2 hours; Tier 4 (Batch/Reporting) < 4 hours | P0 |
| NFR-035 | Recovery Point Objective (RPO) | Tiered model: Tier 1 (Clinical Services) < 5 min; Tier 2 (Supporting Services) < 15 min; Tier 3 (Non-Clinical) < 1 hour; Tier 4 (Batch/Reporting) < 1 hour | P0 |
| NFR-036 | Backup frequency | Continuous replication for database; hourly snapshots for file storage | P0 |
| NFR-037 | Backup testing | Monthly restore test with documented results | P0 |
| NFR-038 | Multi-AZ deployment | All critical services deployed across at least 2 AWS Availability Zones | P0 |
| NFR-039 | Multi-region failover | Active-passive multi-region deployment for disaster recovery | P2 |
| NFR-040 | Planned maintenance window | Zero-downtime deployments via blue/green or rolling update strategy | P0 |

### 6.6 Usability and Accessibility

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-041 | WCAG compliance | WCAG 2.1 Level AA for all user-facing interfaces | P0 |
| NFR-042 | Responsive design | Functional on desktop (1024px+), tablet (768px+), and mobile (375px+) | P0 |
| NFR-043 | Keyboard navigation | All clinical workflows completable via keyboard without a mouse | P0 |
| NFR-044 | Screen reader support | Compatible with JAWS, NVDA, and VoiceOver | P0 |
| NFR-045 | Color contrast | Minimum 4.5:1 contrast ratio for normal text; 3:1 for large text | P0 |
| NFR-046 | Browser support | Chrome (latest 2), Firefox (latest 2), Safari (latest 2), Edge (latest 2) | P0 |
| NFR-047 | Localization readiness | UI framework supports i18n; initial release in English with Spanish as Phase 2 | P1 |
| NFR-048 | System Usability Scale (SUS) | Exceed 68 (industry average) at GA; target 75+ within 12 months post-GA, measured via quarterly SUS surveys of active clinical users | P0 |

### 6.7 Interoperability Standards

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-049 | FHIR version | R4 (4.0.1) | P0 |
| NFR-050 | US Core IG version | v5.0.1 or latest published | P0 |
| NFR-051 | SMART on FHIR version | v2.0 | P1 |
| NFR-052 | Bulk Data Access IG version | v2.0 | P1 |
| NFR-053 | C-CDA version | R2.1 | P1 |
| NFR-054 | HL7v2 version | 2.5.1 | P1 |
| NFR-055 | NCPDP SCRIPT version | 2017071 or later | P1 |
| NFR-056 | Terminology services | SNOMED CT, ICD-10-CM, CPT, LOINC, RxNorm, CVX, NDC via FHIR Terminology Service | P0 |

---

## 7. Data Requirements

### 7.1 Key Data Entities and Relationships

The following entity-relationship summary describes the core data model. All clinical data entities map to FHIR R4 resources.

```
Patient (FHIR: Patient)
  |-- 1:N --> Encounter (FHIR: Encounter)
  |             |-- 1:N --> Condition (FHIR: Condition) [Encounter Diagnosis]
  |             |-- 1:N --> DocumentReference (FHIR: DocumentReference) [Clinical Notes]
  |             |-- 1:N --> MedicationRequest (FHIR: MedicationRequest) [Orders]
  |             |-- 1:N --> ServiceRequest (FHIR: ServiceRequest) [Lab/Imaging/Referral Orders]
  |             |-- 1:N --> Observation (FHIR: Observation) [Vitals, Assessments]
  |             |-- 1:N --> Procedure (FHIR: Procedure)
  |
  |-- 1:N --> Condition (FHIR: Condition) [Problem List - not encounter-specific]
  |-- 1:N --> AllergyIntolerance (FHIR: AllergyIntolerance)
  |-- 1:N --> MedicationStatement (FHIR: MedicationStatement) [Active Medication List]
  |-- 1:N --> Immunization (FHIR: Immunization)
  |-- 1:N --> Coverage (FHIR: Coverage) [Insurance]
  |-- 1:N --> Appointment (FHIR: Appointment)
  |-- 1:N --> Communication (FHIR: Communication) [Messages]
  |-- 1:N --> DiagnosticReport (FHIR: DiagnosticReport) [Results]
  |             |-- 1:N --> Observation (FHIR: Observation) [Individual Results]
  |
  |-- 1:N --> RelatedPerson (FHIR: RelatedPerson) [Emergency Contacts, Proxies]
  |-- 1:N --> Consent (FHIR: Consent)

Practitioner (FHIR: Practitioner)
  |-- 1:N --> PractitionerRole (FHIR: PractitionerRole)

Organization (FHIR: Organization)
  |-- 1:N --> Location (FHIR: Location)
  |-- 1:N --> HealthcareService (FHIR: HealthcareService)

Schedule (FHIR: Schedule)
  |-- 1:N --> Slot (FHIR: Slot)

AuditEvent (FHIR: AuditEvent) [Cross-cutting]
Provenance (FHIR: Provenance) [Cross-cutting]
```

### 7.2 Core Data Entity Details

#### Patient

| Field | Type | FHIR Path | Cardinality | Notes |
|-------|------|-----------|-------------|-------|
| MRN | Identifier | Patient.identifier | 1..* | System-generated, unique |
| Legal Name | HumanName | Patient.name | 1..* | Family + given names |
| Preferred Name | HumanName | Patient.name (use: nickname) | 0..1 | |
| Date of Birth | date | Patient.birthDate | 1..1 | |
| Sex Assigned at Birth | code | Patient.extension (us-core-birthsex) | 1..1 | USCDI |
| Gender Identity | code | Patient.extension (us-core-genderIdentity) | 0..1 | USCDI |
| Race | code | Patient.extension (us-core-race) | 0..1 | USCDI |
| Ethnicity | code | Patient.extension (us-core-ethnicity) | 0..1 | USCDI |
| Preferred Language | code | Patient.communication.language | 0..1 | |
| Address | Address | Patient.address | 0..* | |
| Phone | ContactPoint | Patient.telecom | 0..* | |
| Email | ContactPoint | Patient.telecom | 0..1 | |
| SSN | Identifier | Patient.identifier | 0..1 | Encrypted, masked in UI |
| Photo | Attachment | Patient.photo | 0..1 | |
| Deceased | boolean/dateTime | Patient.deceased[x] | 0..1 | |

#### Encounter

| Field | Type | FHIR Path | Cardinality | Notes |
|-------|------|-----------|-------------|-------|
| Encounter ID | Identifier | Encounter.identifier | 1..1 | System-generated |
| Status | code | Encounter.status | 1..1 | planned, arrived, in-progress, finished, cancelled |
| Class | Coding | Encounter.class | 1..1 | ambulatory, emergency, inpatient, etc. |
| Type | CodeableConcept | Encounter.type | 1..* | Visit type |
| Patient | Reference | Encounter.subject | 1..1 | |
| Participant | BackboneElement | Encounter.participant | 1..* | Providers involved |
| Period | Period | Encounter.period | 1..1 | Start/end times |
| Reason | CodeableConcept | Encounter.reasonCode | 0..* | Chief complaint / reason |
| Diagnosis | BackboneElement | Encounter.diagnosis | 0..* | Encounter diagnoses |
| Location | Reference | Encounter.location | 0..* | |

### 7.3 Data Retention Policies

| Data Category | Minimum Retention | Regulatory Basis | Storage Tier |
|---------------|-------------------|------------------|--------------|
| Medical records (adults) | 10 years from last encounter or as required by most restrictive applicable state law | State medical record retention laws (varies; some require lifetime retention for minors) | Hot storage for 3 years; warm storage for 7 years; cold archive thereafter |
| Medical records (minors) | Age of majority + applicable state retention period (typically age 21 + 3--10 years) | State law | Same as adults |
| Audit logs | 7 years minimum | HIPAA Security Rule (6 years); extended for litigation hold | Warm storage for 1 year; cold archive thereafter |
| Appointment and scheduling data | 7 years | Operational + billing compliance | Warm storage for 2 years; cold archive thereafter |
| Billing records | 10 years | Federal False Claims Act (6 years + 3 years); state laws | Warm for 3 years; cold archive thereafter |
| System logs (non-PHI) | 1 year | Operational | Hot for 30 days; warm for 11 months |
| Backup data | 1 year rolling | Disaster recovery policy | Cold archive |

### 7.4 PHI Handling Requirements

| Requirement | Implementation |
|-------------|----------------|
| PHI at rest encryption | AES-256 via AWS KMS; database-level encryption (RDS/Aurora) + application-level field encryption for SSN, substance abuse data |
| PHI in transit encryption | TLS 1.2+ for all network communications; mutual TLS for service-to-service |
| PHI in logs | Automated PHI detection and redaction before log ingestion; no PHI in application logs |
| PHI in backups | Backups inherit encryption of source data; backup media encrypted with separate KMS key |
| PHI in analytics | De-identification pipeline (Safe Harbor or Expert Determination) before data enters analytics warehouse |
| PHI access logging | Every read/write to a PHI-containing resource generates an AuditEvent |
| PHI disposal | Cryptographic erasure (key destruction) for logical deletion; physical media destruction per NIST SP 800-88 |
| Minimum Necessary | API responses filtered to the minimum data set required for the requestor's purpose and scope |
| Patient right to access | FHIR Patient Access API (real-time programmatic access) and C-CDA export; manual or non-standard format requests fulfilled within 30 days per HIPAA 164.524(b)(2) |
| Patient right to amend | Amendment request workflow with clinician review; both original and amended data retained |
| Accounting of disclosures | Disclosure events logged and reportable for 6 years per HIPAA |
| Business Associate Agreements | All third-party services processing PHI must have executed BAAs; tracked in compliance system |

### 7.5 Terminology and Code Systems

| Code System | Use | Authority |
|-------------|-----|-----------|
| ICD-10-CM | Diagnoses, problem list | CMS/WHO |
| SNOMED CT | Clinical findings, procedures, substances | SNOMED International |
| CPT | Procedures, billing | AMA |
| LOINC | Laboratory tests, clinical observations | Regenstrief Institute |
| RxNorm | Medications | NLM |
| NDC | Drug products | FDA |
| CVX | Vaccine codes (vaccines administered) | CDC |
| MVX | Vaccine manufacturer codes | CDC |
| HCPCS | Supplies, services | CMS |
| NUBC Revenue Codes | Billing | NUBC |

---

## 8. Integration Requirements

### 8.1 FHIR R4 API Specification

#### Supported Resources and Operations

| Resource | Read | Search | Create | Update | Delete | Patch |
|----------|------|--------|--------|--------|--------|-------|
| Patient | Yes | Yes | Yes | Yes | No* | Yes |
| Encounter | Yes | Yes | Yes | Yes | No | Yes |
| Condition | Yes | Yes | Yes | Yes | No | Yes |
| AllergyIntolerance | Yes | Yes | Yes | Yes | No | Yes |
| MedicationRequest | Yes | Yes | Yes | Yes | No | Yes |
| Medication | Yes | Yes | Yes | Yes | No | No |
| MedicationAdministration | Yes | Yes | Yes | Yes | No | No |
| ServiceRequest | Yes | Yes | Yes | Yes | No | Yes |
| Observation | Yes | Yes | Yes | Yes | No | Yes |
| DiagnosticReport | Yes | Yes | Yes | Yes | No | No |
| DocumentReference | Yes | Yes | Yes | Yes | No | No |
| Immunization | Yes | Yes | Yes | Yes | No | Yes |
| Procedure | Yes | Yes | Yes | Yes | No | Yes |
| Practitioner | Yes | Yes | Yes | Yes | No | Yes |
| PractitionerRole | Yes | Yes | Yes | Yes | No | Yes |
| Organization | Yes | Yes | Yes | Yes | No | Yes |
| Location | Yes | Yes | Yes | Yes | No | Yes |
| Appointment | Yes | Yes | Yes | Yes | No | Yes |
| Schedule | Yes | Yes | Yes | Yes | No | No |
| Slot | Yes | Yes | Yes | Yes | No | No |
| Coverage | Yes | Yes | Yes | Yes | No | Yes |
| Communication | Yes | Yes | Yes | Yes | No | No |
| Provenance | Yes | Yes | Yes | No | No | No |
| AuditEvent | Yes | Yes | Yes | No | No | No |

*Patient records are logically deleted (status set to inactive), never physically deleted.

#### Search Parameters

All search parameters defined in US Core IG v5.0+ are supported, including:

- `Patient`: name, family, given, birthdate, gender, identifier, phone, email, address
- `Condition`: patient, clinical-status, onset-date, code, category
- `Observation`: patient, category, code, date, status, value-quantity
- `MedicationRequest`: patient, status, intent, authoredon, medication

#### Authentication and Authorization

```
Authorization Flow: OAuth 2.0 Authorization Code with PKCE
Token Endpoint: POST /oauth2/token
Authorization Endpoint: GET /oauth2/authorize
Scopes: SMART on FHIR v2 scopes
  - patient/*.read   (patient-facing apps)
  - user/*.read      (clinician-facing apps)
  - user/*.write     (clinician-facing apps)
  - system/*.read    (backend services)
  - launch           (EHR launch)
  - launch/patient   (patient context)
  - openid, fhirUser, profile (identity)
```

#### Rate Limiting

| Client Type | Rate Limit | Burst Limit |
|-------------|------------|-------------|
| Patient-facing app | 60 requests/minute | 10 requests/second |
| Clinician-facing app | 300 requests/minute | 30 requests/second |
| SMART on FHIR app | 300 requests/minute (inherits from user context) | 30 requests/second |
| Backend service | 1,000 requests/minute | 100 requests/second |
| Bulk Data export | 10 concurrent exports; 1M resources per export |  |

### 8.2 HL7v2 Interfaces

| Interface | Direction | Message Type | Transport | Trigger |
|-----------|-----------|--------------|-----------|---------|
| ADT Feed (outbound) | Out | ADT^A01, A02, A03, A04, A08 | MLLP/TLS | Patient admission, transfer, discharge, registration, update |
| ADT Feed (inbound) | In | ADT^A01, A02, A03, A04, A08 | MLLP/TLS | Hospital ADT events |
| Lab Orders (outbound) | Out | ORM^O01 or OML^O21 | MLLP/TLS | Laboratory order placed |
| Lab Results (inbound) | In | ORU^R01 | MLLP/TLS | Lab result available |
| Radiology Orders (outbound) | Out | ORM^O01 | MLLP/TLS | Imaging order placed |
| Radiology Results (inbound) | In | ORU^R01 | MLLP/TLS | Radiology report available |
| Scheduling (outbound) | Out | SIU^S12, S13, S14, S15 | MLLP/TLS | Appointment CRUD |
| Transcription (inbound) | In | MDM^T02 | MLLP/TLS | Transcribed document available |

#### HL7v2 Interface Engine

- An integration engine (e.g., built-in or via Mirth Connect/Rhapsody) manages message routing, transformation, and monitoring.
- Message queuing with configurable retry logic (exponential backoff, max retries, dead-letter queue).
- Failed messages are quarantined with error classification and manual resubmission capability.
- Interface monitoring dashboard shows message volumes, success/failure rates, and latency.

### 8.3 External System Integrations

#### 8.3.1 Reference Laboratories

| Aspect | Specification |
|--------|---------------|
| Protocol | HL7v2 (ORM^O01 outbound, ORU^R01 inbound) or FHIR (ServiceRequest, DiagnosticReport) |
| Labs | Quest Diagnostics, Labcorp, regional reference labs |
| Data mapping | LOINC-coded test codes; patient demographics; insurance; ordering provider NPI |
| Result handling | Automatic filing to patient chart; abnormal/critical flagging; provider notification |

#### 8.3.2 Pharmacy Network

| Aspect | Specification |
|--------|---------------|
| Protocol | NCPDP SCRIPT 2017071 via Surescripts network |
| Functions | NewRx, RxRenewalRequest/Response, CancelRx, RxFill, EPCS |
| Certification | Surescripts certification for e-Prescribing and EPCS |
| Formulary | NCPDP Real-Time Prescription Benefit (RTPB) |

#### 8.3.3 Health Information Exchanges (HIEs)

| Aspect | Specification |
|--------|---------------|
| Protocol | IHE XDS.b/XCA (document sharing), IHE PDQ/PIX (patient matching) |
| Networks | Commonwell Health Alliance, Carequality, state HIEs |
| Document types | C-CDA CCD, Referral Note, Discharge Summary |
| Consent | Configurable opt-in/opt-out per jurisdictional requirements |

#### 8.3.4 Payer / Insurance

| Aspect | Specification |
|--------|---------------|
| Protocol | X12 270/271 (eligibility), X12 837 (claims), X12 835 (remittance) |
| Functions | Real-time eligibility verification, claim submission, remittance reconciliation |
| Clearinghouse | Integration via clearinghouse API (e.g., Availity, Change Healthcare) |

#### 8.3.5 Immunization Registries

| Aspect | Specification |
|--------|---------------|
| Protocol | HL7v2 VXU^V04 (outbound), HL7v2 RSP^K11 (inbound query response) |
| Registries | State immunization information systems (IIS) |
| Functions | Report administered immunizations; query patient immunization history |

#### 8.3.6 Public Health Reporting

| Aspect | Specification |
|--------|---------------|
| Protocol | HL7v2 (ORU^R01 for reportable conditions), FHIR (electronic case reporting -- eCR) |
| Reporting | Electronic initial case reports (eICR) to AIMS/RCKMS platform |
| Conditions | Automatically trigger reportable condition detection using RCTC value sets |

---

## 9. Compliance Requirements Matrix

### 9.1 HIPAA Security Rule Mapping

| HIPAA Requirement | CFR Reference | OpenMedRecord Control | FR/NFR Reference |
|-------------------|---------------|----------------------|------------------|
| Access controls | 164.312(a)(1) | RBAC with granular permissions; unique user IDs; emergency access (break-the-glass); auto-logoff | FR-075, FR-078, FR-079 |
| Audit controls | 164.312(b) | Comprehensive, immutable audit trail; 7-year retention; tamper-evident logging | FR-077, FR-082 |
| Integrity controls | 164.312(c)(1) | Data integrity verification via checksums; signed clinical documents; change-versioning | FR-017, FR-018, FR-019 |
| Transmission security | 164.312(e)(1) | TLS 1.2+ for all transmissions; encryption of PHI in transit | NFR-018 |
| Encryption at rest | 164.312(a)(2)(iv) | AES-256 encryption for all PHI at rest; customer-managed KMS keys | NFR-017, FR-080 |
| Person or entity authentication | 164.312(d) | MFA for all users; FIPS 140-2 for EPCS; SAML/OIDC federation | FR-076, NFR-019 |
| Workforce security | 164.308(a)(3) | Role-based access; onboarding/offboarding workflows; access reviews | FR-075 |
| Security incident procedures | 164.308(a)(6) | Automated anomaly detection; incident response playbooks; breach notification workflow | NFR-022, NFR-023 |
| Contingency plan | 164.308(a)(7) | Multi-AZ deployment; automated backups; tested DR procedures; tiered RTO/RPO (Tier 1 Clinical: RTO < 15min, RPO < 5min) | NFR-034, NFR-035, NFR-036, NFR-037, NFR-038 |
| Business associate contracts | 164.308(b)(1) | BAA tracking system; all third-party services with PHI access have executed BAAs | Operational |
| Facility access controls | 164.310(a)(1) | AWS data center physical security (SOC 2 Type II certified) | Infrastructure |
| Workstation security | 164.310(b) | Session timeout; screen lock; device policy enforcement | FR-079 |
| Device and media controls | 164.310(d)(1) | Encrypted backups; cryptographic erasure; no PHI on removable media | NFR-017 |

### 9.2 SOC 2 Trust Service Criteria Mapping

| TSC Category | Criteria | OpenMedRecord Control | FR/NFR Reference |
|--------------|----------|----------------------|------------------|
| **Security** | CC6.1 - Logical access security | RBAC, MFA, OAuth 2.0, session management | FR-075, FR-076, FR-079, NFR-020 |
| | CC6.2 - Prior to registration/authorization | User provisioning workflow with manager approval; application registration with org approval | FR-075, US-INT-002 |
| | CC6.3 - Registration/authorization | Unique user IDs; SMART on FHIR client registration; scope-based authorization | FR-075, FR-084 |
| | CC6.6 - Restrict access to PHI | Minimum necessary enforcement; field-level access control; break-the-glass controls | FR-078, NFR-025 |
| | CC6.7 - Transmission restrictions | TLS 1.2+; encrypted APIs; mTLS for service-to-service | NFR-018 |
| | CC6.8 - Prevent unauthorized software | CI/CD pipeline with code review; signed artifacts; container image scanning | NFR-022 |
| | CC7.1 - Detect and monitor | Centralized logging (CloudWatch, CloudTrail); SIEM integration; anomaly detection | FR-077, NFR-022 |
| | CC7.2 - Monitor system components | Infrastructure monitoring; application performance monitoring; alerting | NFR-033 |
| | CC7.3 - Evaluate detected events | Security incident response procedures; severity classification; escalation paths | Operational |
| | CC7.4 - Respond to incidents | Incident response playbook; breach notification procedures; forensic capabilities | Operational |
| **Availability** | A1.1 - Availability commitments | 99.9% SLA; multi-AZ deployment; auto-scaling | NFR-033, NFR-038 |
| | A1.2 - Environmental protections | AWS managed infrastructure; multi-AZ; automated failover | NFR-038 |
| | A1.3 - Recovery procedures | Tested backup/restore; tiered RTO/RPO (Tier 1 Clinical: RTO < 15min, RPO < 5min) | NFR-034, NFR-035, NFR-037 |
| **Processing Integrity** | PI1.1 - Complete and accurate processing | Data validation; referential integrity; FHIR profile validation | FR-010, FR-033 |
| **Confidentiality** | C1.1 - Confidential information identification | PHI classification tags; data dictionary; sensitivity levels | NFR-025 |
| | C1.2 - Confidential information disposal | Cryptographic erasure; retention policy enforcement; automated lifecycle management | Section 7.3 |
| **Privacy** | P1--P8 | Patient consent management; access controls; disclosure logging; amendment workflows; breach notification | FR-075, FR-077, Section 7.4 |

### 9.3 HITRUST CSF Control Mapping

| HITRUST Domain | Key Controls | OpenMedRecord Implementation | FR/NFR Reference |
|----------------|-------------|------------------------------|------------------|
| 01 - Information Security Management | 01.a - Security policy; 01.b - Review | Documented security policies in repo; annual review cycle | Operational |
| 02 - Access Control | 02.a - Business requirement; 02.d - User registration; 02.i - MFA | RBAC; automated provisioning; MFA enforcement | FR-075, FR-076 |
| 03 - Human Resources Security | 03.a - Roles and responsibilities; 03.c - Termination | Onboarding/offboarding automation; immediate access revocation | FR-075 |
| 05 - Asset Management | 05.a - Inventory; 05.b - Classification | CMDB; PHI data classification; resource tagging | NFR-025 |
| 06 - Communications and Operations | 06.d - Separation of environments; 06.e - Malware protection | Isolated dev/staging/prod; WAF; container scanning | NFR-022, NFR-024 |
| 07 - Information Systems Acquisition | 07.a - Security requirements; 07.e - Secure development | Security in SDLC; SAST/DAST; code review | NFR-022 |
| 08 - Incident Management | 08.a - Reporting; 08.b - Weaknesses | Incident response plan; vulnerability disclosure program | Operational |
| 09 - Business Continuity | 09.a - BCM process; 09.b - Risk assessment | DR plan; multi-AZ; tested failover | NFR-034--NFR-039 |
| 10 - Compliance | 10.a - Legal requirements; 10.d - Data protection | HIPAA controls; audit logging; encryption; privacy policies | NFR-026--NFR-032 |
| 11 - Information Security Risk Management | 11.a - Risk assessment | Annual risk assessment; continuous vulnerability scanning | NFR-022, NFR-023 |

### 9.4 ONC Certification Criteria Mapping

| ONC Criterion | Description | OpenMedRecord Capability | FR Reference |
|---------------|-------------|--------------------------|--------------|
| 170.315(a)(1) | CPOE - Medications | Medication order entry with drug interaction checking | FR-025, FR-026 |
| 170.315(a)(2) | CPOE - Laboratory | Lab order entry with LOINC coding | FR-027 |
| 170.315(a)(3) | CPOE - Imaging | Imaging order entry with AUC | FR-028, FR-029 |
| 170.315(a)(5) | Demographics | Patient demographics with USCDI data elements | FR-001 |
| 170.315(a)(9) | Clinical decision support | Drug interaction alerts; preventive care reminders; configurable rules | FR-049--FR-054 |
| 170.315(a)(14) | Implantable device list | UDI tracking (planned) | Planned |
| 170.315(b)(1) | Transitions of care | C-CDA generation and consumption; Direct messaging | FR-087, FR-089 |
| 170.315(b)(2) | Clinical information reconciliation | Medication, allergy, and problem reconciliation from C-CDA | FR-038 |
| 170.315(b)(3) | E-Prescribing | NCPDP SCRIPT; EPCS | FR-034, FR-035 |
| 170.315(b)(10) | EHI export | FHIR Bulk Data Export; EHI export for entire patient record | FR-088 |
| 170.315(c)(1--3) | CQMs | eCQM calculation; QRDA I/III export | FR-069, FR-070 |
| 170.315(d)(1) | Authentication | MFA; unique user credentials | FR-076 |
| 170.315(d)(2) | Auditable events | Comprehensive audit trail | FR-077 |
| 170.315(d)(7) | End-user device encryption | TLS for data in transit | NFR-018 |
| 170.315(d)(9) | Trusted connection | TLS 1.2+; certificate-based trust | NFR-018 |
| 170.315(d)(13) | Multi-factor authentication | MFA enforcement | FR-076 |
| 170.315(g)(7) | Application access - Patient selection | SMART on FHIR patient context | FR-084 |
| 170.315(g)(9) | Application access - All data | FHIR API with US Core | FR-083 |
| 170.315(g)(10) | Standardized API for patient and population services | FHIR R4 API; US Core; SMART; Bulk Data | FR-083, FR-084, FR-085, FR-088 |

---

## 10. Release Plan and Phasing

### 10.1 Phase 1 -- MVP (Months 1--9)

**Goal:** Deliver a production-ready EHR with core clinical workflows, foundational security, and basic interoperability sufficient for ambulatory practice operations.

**Target:** Limited availability (design partners) at Month 7; General Availability at Month 9.

#### Phase 1 Scope

| Module | Capabilities | Key Requirements |
|--------|-------------|------------------|
| **Patient Management** | Registration, search, demographics, insurance (manual verification), duplicate detection | FR-001 through FR-006, FR-010 |
| **Clinical Documentation** | SOAP notes, pre-built templates, note signing with MFA, addendums, problem list, allergy list | FR-011 through FR-015, FR-017 through FR-019, FR-022 through FR-024 |
| **Vital Signs** | Vital signs entry with auto-calculated BMI, abnormal value flagging, trend charting | FR-VS-001, FR-VS-002, FR-VS-003 |
| **Encounter Management** | Encounter creation, status workflow, clinical data association | FR-ENC-001, FR-ENC-002 |
| **Basic Order Entry** | Medication orders with drug interaction checking, laboratory orders | FR-025 through FR-027, FR-033 |
| **Scheduling** | Appointment scheduling, rescheduling, cancellation, automated reminders | FR-041 through FR-044, FR-048 |
| **Security & Access Control** | RBAC, MFA, audit trail, break-the-glass, session management, encryption | FR-075 through FR-082 |
| **User & Role Management** | User CRUD, custom roles with granular permissions, provisioning workflow, quarterly access reviews | FR-UM-001, FR-UM-002, FR-UM-003 |
| **Consent Management (General)** | Consent recording, enforcement at data access layer, consent withdrawal | FR-CON-001, FR-CON-002 |
| **Interoperability (Foundation)** | FHIR R4 API (US Core), SMART on FHIR authorization, CapabilityStatement | FR-083, FR-084, FR-091 |
| **Infrastructure** | AWS deployment (multi-AZ), CI/CD pipeline, monitoring, backup/restore | NFR-001 through NFR-006, NFR-012, NFR-017, NFR-018, NFR-033 through NFR-038 |

#### Phase 1 Milestones

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| M1.1 | Month 1 | Architecture design complete; ADR repository initialized |
| M1.2 | Month 2 | Development environment and CI/CD pipeline operational |
| M1.3 | Month 3 | Patient management and scheduling modules feature-complete |
| M1.4 | Month 4 | Clinical documentation module feature-complete |
| M1.5 | Month 5 | Security module and FHIR API feature-complete |
| M1.6 | Month 6 | Basic order entry feature-complete; integration testing begins |
| M1.7 | Month 7 | Design partner deployments (limited availability) |
| M1.8 | Month 8 | Performance testing; security audit; bug fixes |
| M1.9 | Month 9 | General Availability release (v1.0) |

#### Phase 1 Exit Criteria

- All P0 functional requirements pass acceptance testing.
- Security penetration test completed with no critical or high findings unresolved.
- Performance benchmarks met (NFR-001 through NFR-006).
- 99.9% uptime demonstrated over 30 continuous days in staging.
- At least 2 design partner organizations have operated the system for 30+ days.
- HIPAA Security Rule self-assessment completed with no critical gaps.

---

### 10.2 Phase 2 -- Clinical Depth (Months 10--18)

**Goal:** Achieve ONC Health IT Certification; deliver advanced clinical workflows, patient-facing portal, and comprehensive interoperability.

#### Phase 2 Scope

| Module | Capabilities | Key Requirements |
|--------|-------------|------------------|
| **CPOE (Full)** | Imaging orders with AUC, referral orders, order sets | FR-028 through FR-032 |
| **Medication Management** | E-prescribing (NCPDP SCRIPT), EPCS, RxFill, medication reconciliation, MAR | FR-034 through FR-040 |
| **Clinical Decision Support** | Drug interaction alerts (enhanced), preventive care reminders, duplicate order detection, configurable rules | FR-049 through FR-054 |
| **Results Management** | Lab result review/trending, critical value notification, result routing, imaging result viewing | FR-055 through FR-061 |
| **Patient Portal** | Health record access, secure messaging, appointment management, pre-visit questionnaires, record export | FR-062 through FR-065, FR-068 |
| **Reporting (Foundation)** | eCQM calculation and QRDA export | FR-069, FR-070 |
| **Interoperability (Extended)** | SMART App Launch, HL7v2 interfaces, C-CDA exchange, Bulk Data export, Direct messaging | FR-085 through FR-089 |
| **Scheduling (Extended)** | Patient self-scheduling, resource management | FR-045, FR-046 |
| **Custom Templates** | Advanced template engine with smart macros and conditional logic | FR-016 |
| **Co-signature** | Supervised clinician signature workflows | FR-020 |
| **Insurance Verification** | Real-time X12 270/271 eligibility checking | FR-007 |
| **Patient Merge** | Full duplicate merge with reversibility | FR-008 |
| **Immunization Management** | Immunization recording with CVX/MVX codes, history, forecasting per CDC schedule | FR-IMM-001, FR-IMM-002 |
| **Consent Management (42 CFR Part 2)** | SUD consent workflows per 42 CFR 2.31, re-disclosure prohibition notices | FR-CON-003, FR-CON-004 |
| **Psychotherapy Notes** | Distinct data classification, separate storage, exclusion from standard disclosures and bulk exports | FR-PSY-001, FR-PSY-002 |

#### Phase 2 Milestones

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| M2.1 | Month 10 | Phase 2 design and architecture for new modules complete |
| M2.2 | Month 12 | E-prescribing and medication management feature-complete |
| M2.3 | Month 13 | CDS, results management feature-complete |
| M2.4 | Month 14 | Patient portal feature-complete |
| M2.5 | Month 15 | HL7v2 interfaces and C-CDA exchange feature-complete |
| M2.6 | Month 16 | ONC Certification testing begins |
| M2.7 | Month 17 | SOC 2 Type II audit begins |
| M2.8 | Month 18 | Phase 2 release (v2.0); ONC Certification achieved |

#### Phase 2 Exit Criteria

- All P1 functional requirements pass acceptance testing.
- ONC Health IT Certification (2015 Edition Cures Update) granted.
- SOC 2 Type II audit completed with clean opinion.
- Surescripts e-Prescribing and EPCS certification achieved.
- Patient portal passes WCAG 2.1 AA accessibility audit.
- System supports 10,000 concurrent users (load test verified).
- At least 10 organizations operating in production.

---

### 10.3 Phase 3 -- Differentiation (Months 19--27)

**Goal:** Deliver advanced analytics, population health management, telehealth, and ecosystem enablement features that differentiate OpenMedRecord from competing solutions.

#### Phase 3 Scope

| Module | Capabilities | Key Requirements |
|--------|-------------|------------------|
| **Advanced Reporting & Analytics** | Operational dashboards, ad hoc report builder, scheduled reports | FR-071, FR-073, FR-074 |
| **Population Health** | Population queries, risk stratification, panel management, care gap analysis | FR-072 |
| **Patient Portal (Extended)** | Proxy access, online bill pay, payment plans | FR-066, FR-067 |
| **Interoperability (Advanced)** | HIE connectivity (IHE profiles), immunization registry, public health reporting (eCR) | FR-090 |
| **Telehealth** | Integrated video visits, virtual waiting room, screen sharing, documentation integration | New FRs (TBD) |
| **Voice Dictation** | AI-assisted documentation with speech-to-text | FR-021 |
| **AI-Assisted Documentation** | Ambient listening, note summarization, suggested coding | New FRs (TBD) |
| **Waitlist Management** | Automated waitlist with patient notification | FR-047 |
| **Multi-Region DR** | Active-passive multi-region failover | NFR-039 |
| **Localization** | Spanish language support | NFR-047 |
| **HITRUST Certification** | HITRUST CSF r2 certification | NFR-028 |
| **Photo Capture** | Patient photograph capture and storage | FR-009 |
| **Formulary Checking** | Real-time formulary and patient cost display | FR-037 |
| **CDS Hooks** | External CDS integration via CDS Hooks | FR-054 |
| **Infobutton** | Contextual clinical guideline links | FR-051 |

#### Phase 3 Milestones

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| M3.1 | Month 19 | Phase 3 design; telehealth vendor selection |
| M3.2 | Month 21 | Population health and analytics feature-complete |
| M3.3 | Month 23 | Telehealth integration feature-complete |
| M3.4 | Month 24 | AI-assisted documentation beta |
| M3.5 | Month 25 | HIE connectivity and public health reporting feature-complete |
| M3.6 | Month 26 | HITRUST certification assessment |
| M3.7 | Month 27 | Phase 3 release (v3.0) |

#### Phase 3 Exit Criteria

- All P2 functional requirements pass acceptance testing.
- HITRUST CSF r2 certification achieved.
- Telehealth visits successfully conducted in production.
- Population health dashboards validated against manual chart review (>95% accuracy).
- AI documentation features validated by clinical advisory board.
- At least 50 organizations operating in production.
- Active SMART on FHIR app ecosystem with 10+ registered applications.

---

### 10.4 Summary Timeline

```
Month:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
        |------ Phase 1 (MVP) ------|  |---------- Phase 2 (Clinical Depth) ---------|  |------ Phase 3 (Differentiation) ------|
        [================= v1.0 GA ==]  [================================= v2.0 GA ===]  [================================ v3.0 =]
                              ^                                               ^                                            ^
                          LA (M7)                                      ONC Cert (M18)                              HITRUST (M27)
```

**LA** = Limited Availability; **GA** = General Availability

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| ADT | Admit, Discharge, Transfer -- HL7v2 message category for patient movement events |
| AUC | Appropriate Use Criteria -- CMS-mandated clinical decision support for advanced imaging orders |
| BAA | Business Associate Agreement -- HIPAA-required contract with entities handling PHI |
| C-CDA | Consolidated Clinical Document Architecture -- HL7 standard for clinical document exchange |
| CDS | Clinical Decision Support |
| CDS Hooks | HL7 standard for integrating external decision support into EHR workflows |
| CMK | Customer-Managed Key (AWS KMS) |
| CPOE | Computerized Provider Order Entry |
| CQL | Clinical Quality Language -- HL7 standard for expressing clinical logic |
| DAST | Dynamic Application Security Testing |
| DICOM | Digital Imaging and Communications in Medicine |
| eCQM | electronic Clinical Quality Measure |
| EHR | Electronic Health Record |
| EHI | Electronic Health Information |
| EPCS | Electronic Prescribing of Controlled Substances |
| FHIR | Fast Healthcare Interoperability Resources (HL7 standard) |
| HITRUST CSF | Health Information Trust Alliance Common Security Framework |
| HIE | Health Information Exchange |
| HL7 | Health Level Seven International -- standards development organization |
| IHE | Integrating the Healthcare Enterprise -- standards profiling organization |
| LOINC | Logical Observation Identifiers Names and Codes |
| MAR | Medication Administration Record |
| MLLP | Minimum Lower Layer Protocol -- transport protocol for HL7v2 |
| MRN | Medical Record Number |
| NCPDP | National Council for Prescription Drug Programs |
| NPI | National Provider Identifier |
| QRDA | Quality Reporting Document Architecture |
| RBAC | Role-Based Access Control |
| RPO | Recovery Point Objective |
| RTPB | Real-Time Prescription Benefit |
| RTO | Recovery Time Objective |
| RxNorm | Normalized names for clinical drugs (NLM) |
| SAST | Static Application Security Testing |
| SMART | Substitutable Medical Applications, Reusable Technologies |
| SNOMED CT | Systematized Nomenclature of Medicine -- Clinical Terms |
| SOAP | Subjective, Objective, Assessment, Plan (clinical note format) |
| SOC 2 | Service Organization Control Type 2 |
| SUS | System Usability Scale |
| TLS | Transport Layer Security |
| USCDI | United States Core Data for Interoperability |
| USPSTF | United States Preventive Services Task Force |
| WCAG | Web Content Accessibility Guidelines |

---

## Appendix B: Open Questions and Decisions Needed

| ID | Question | Owner | Status | Decision |
|----|----------|-------|--------|----------|
| OQ-001 | Which drug knowledge base vendor should be integrated (First Databank vs. Medi-Span vs. open-source)? | Product/Engineering | Open | -- |
| OQ-002 | Should the system support on-premises deployment in Phase 1, or defer to Phase 2? | Product | Open | -- |
| OQ-003 | Which Surescripts certification pathway (direct vs. via certified intermediary) should be pursued? | Engineering | Open | -- |
| OQ-004 | Should AI-assisted documentation (ambient listening) be a core feature or a SMART on FHIR plugin? | Product | Open | -- |
| OQ-005 | What is the strategy for managing state-specific medical record retention requirements (50 states)? | Compliance | Open | -- |
| OQ-006 | Should the patient portal be a standalone SPA or integrated into the main application? | Engineering | Open | -- |
| OQ-007 | What is the telehealth vendor integration strategy (build vs. buy vs. partner)? | Product | Open | -- |
| OQ-008 | How will the project sustain itself financially (foundation model, commercial support, dual licensing)? | Leadership | Open | -- |

---

## Appendix C: References

1. HL7 FHIR R4 Specification: https://hl7.org/fhir/R4/
2. US Core Implementation Guide v5.0.1: https://hl7.org/fhir/us/core/
3. SMART App Launch Framework v2.0: https://hl7.org/fhir/smart-app-launch/
4. FHIR Bulk Data Access IG v2.0: https://hl7.org/fhir/uv/bulkdata/
5. ONC Health IT Certification Program: https://www.healthit.gov/topic/certification-ehrs/certification-health-it
6. HIPAA Security Rule: 45 CFR Part 160 and Part 164, Subparts A and C
7. HITRUST CSF: https://hitrustalliance.net/hitrust-csf/
8. NCPDP SCRIPT Standard: https://www.ncpdp.org/
9. WCAG 2.1: https://www.w3.org/TR/WCAG21/
10. USCDI v3: https://www.healthit.gov/isa/united-states-core-data-interoperability-uscdi
11. CDS Hooks: https://cds-hooks.hl7.org/
12. IHE Technical Frameworks: https://www.ihe.net/resources/technical_frameworks/

---

*This document is maintained in version control. For the latest version, see the repository at the canonical source. All contributions are subject to the project's Apache 2.0 license.*
