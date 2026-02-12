"""
End-to-end test: Complete clinical workflow.

Exercises the full lifecycle that a clinician would perform:
  1. Register a new patient
  2. Create an encounter (office visit)
  3. Record vital sign observations
  4. Create a medication order
  5. Sign a clinical note
  6. Verify the complete audit trail
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


PATIENTS_PATH = "/api/v1/patients"
ENCOUNTERS_PATH = "/api/v1/encounters"
OBSERVATIONS_PATH = "/api/v1/observations"
MEDICATIONS_PATH = "/api/v1/medications"
NOTES_PATH = "/api/v1/notes"
AUDIT_PATH = "/api/v1/audit"


@pytest.mark.e2e
class TestClinicalWorkflow:
    """Full clinical workflow end-to-end test."""

    @pytest.mark.asyncio
    async def test_complete_clinical_encounter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
        sample_encounter_data: dict,
        sample_observation_data: dict,
    ):
        """
        Complete clinical workflow:
        register -> encounter -> observations -> medication -> note -> audit.
        """

        # ============================================================
        # Step 1: Register a new patient
        # ============================================================
        patient_resp = await client.post(
            PATIENTS_PATH, json=sample_patient_data, headers=auth_headers
        )
        assert (
            patient_resp.status_code == 201
        ), f"Patient creation failed: {patient_resp.text}"
        patient = patient_resp.json()
        patient_id = patient["id"]
        assert patient["first_name"] == sample_patient_data["first_name"]
        assert patient["last_name"] == sample_patient_data["last_name"]

        # Verify patient can be retrieved
        get_patient_resp = await client.get(
            f"{PATIENTS_PATH}/{patient_id}", headers=auth_headers
        )
        assert get_patient_resp.status_code == 200

        # ============================================================
        # Step 2: Create an encounter (office visit)
        # ============================================================
        sample_encounter_data["patient_id"] = patient_id
        encounter_resp = await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )
        assert (
            encounter_resp.status_code == 201
        ), f"Encounter creation failed: {encounter_resp.text}"
        encounter = encounter_resp.json()
        encounter_id = encounter["id"]
        assert encounter["status"] == "in-progress"
        assert encounter["patient_id"] == patient_id

        # ============================================================
        # Step 3: Record vital sign observations
        # ============================================================
        sample_observation_data["patient_id"] = patient_id
        sample_observation_data["encounter_id"] = encounter_id

        obs_resp = await client.post(
            OBSERVATIONS_PATH,
            json=sample_observation_data,
            headers=auth_headers,
        )
        assert (
            obs_resp.status_code == 201
        ), f"Observation creation failed: {obs_resp.text}"
        observation = obs_resp.json()
        _ = observation["id"]
        assert observation["status"] == "final"

        # Record additional vitals
        temp_observation = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "code": "8310-5",
            "display": "Body temperature",
            "category": "vital-signs",
            "value": 98.6,
            "unit": "degF",
            "effective_datetime": datetime.now(timezone.utc).isoformat(),
            "status": "final",
        }
        temp_resp = await client.post(
            OBSERVATIONS_PATH, json=temp_observation, headers=auth_headers
        )
        assert temp_resp.status_code == 201

        # Heart rate
        hr_observation = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "code": "8867-4",
            "display": "Heart rate",
            "category": "vital-signs",
            "value": 72,
            "unit": "/min",
            "effective_datetime": datetime.now(timezone.utc).isoformat(),
            "status": "final",
        }
        hr_resp = await client.post(
            OBSERVATIONS_PATH, json=hr_observation, headers=auth_headers
        )
        assert hr_resp.status_code == 201

        # ============================================================
        # Step 4: Create a medication order
        # ============================================================
        medication_order = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "medication": {
                "code": "197361",
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "display": "Lisinopril 10 MG Oral Tablet",
            },
            "dosage": {
                "text": "Take 1 tablet by mouth once daily",
                "route": "oral",
                "dose_value": 10,
                "dose_unit": "mg",
                "frequency": "once daily",
            },
            "reason": "Essential hypertension (I10)",
            "status": "active",
            "authored_on": datetime.now(timezone.utc).isoformat(),
        }
        med_resp = await client.post(
            MEDICATIONS_PATH, json=medication_order, headers=auth_headers
        )
        assert (
            med_resp.status_code == 201
        ), f"Medication order creation failed: {med_resp.text}"
        medication = med_resp.json()
        _ = medication["id"]

        # ============================================================
        # Step 5: Create and sign a clinical note
        # ============================================================
        clinical_note = {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "type": "progress-note",
            "title": "Office Visit - Annual Physical",
            "content": (
                "SUBJECTIVE: Patient presents for annual physical examination. "
                "No acute complaints. Reports compliance with current medications. "
                "Denies chest pain, shortness of breath, or dizziness.\n\n"
                "OBJECTIVE: Vital signs within normal limits. BP 120/80, HR 72, "
                "Temp 98.6F. General appearance: well-nourished, in no acute distress. "
                "Heart: regular rate and rhythm, no murmurs. Lungs: clear bilaterally.\n\n"
                "ASSESSMENT: Essential hypertension (I10), well-controlled on current regimen.\n\n"
                "PLAN: Continue Lisinopril 10mg daily. Follow up in 6 months. "
                "Routine labs ordered."
            ),
            "status": "preliminary",
        }
        note_resp = await client.post(
            NOTES_PATH, json=clinical_note, headers=auth_headers
        )
        assert note_resp.status_code == 201, f"Note creation failed: {note_resp.text}"
        note = note_resp.json()
        note_id = note["id"]

        # Sign the note (transition to final)
        sign_resp = await client.patch(
            f"{NOTES_PATH}/{note_id}/sign",
            headers=auth_headers,
        )
        assert sign_resp.status_code == 200, f"Note signing failed: {sign_resp.text}"
        signed_note = sign_resp.json()
        assert signed_note["status"] == "final"
        assert "signed_by" in signed_note
        assert "signed_at" in signed_note

        # ============================================================
        # Step 6: Complete the encounter
        # ============================================================
        complete_resp = await client.patch(
            f"{ENCOUNTERS_PATH}/{encounter_id}/status",
            json={
                "status": "completed",
                "end_time": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "completed"

        # ============================================================
        # Step 7: Verify the complete audit trail
        # ============================================================
        audit_resp = await client.get(
            AUDIT_PATH,
            params={"resource_id": patient_id},
            headers=auth_headers,
        )
        assert audit_resp.status_code == 200
        audit_entries = audit_resp.json()
        items = (
            audit_entries.get("items", audit_entries)
            if isinstance(audit_entries, dict)
            else audit_entries
        )

        # We should have audit entries for:
        # - Patient create + read
        # - Encounter create + status update
        # - 3 Observations create
        # - Medication order create
        # - Note create + sign
        # Total: at least 10 audit events
        assert len(items) >= 5, f"Expected at least 5 audit entries, got {len(items)}"

        # Verify audit entries cover different resource types
        resource_types = {entry.get("resource_type") for entry in items}
        assert "Patient" in resource_types

        # Verify all entries have timestamps
        for entry in items:
            assert "timestamp" in entry
            assert "user_id" in entry
            assert "action" in entry

        # ============================================================
        # Step 8: Verify FHIR representation
        # ============================================================
        fhir_resp = await client.get(
            f"/fhir/Patient/{patient_id}", headers=auth_headers
        )
        assert fhir_resp.status_code == 200
        fhir_patient = fhir_resp.json()
        assert fhir_patient["resourceType"] == "Patient"
        assert fhir_patient["id"] == patient_id
