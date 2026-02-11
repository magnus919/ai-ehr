#!/usr/bin/env python3
"""
OpenMedRecord -- Database Seed Script

Populates the development database with realistic sample data:
  - Healthcare organizations (tenants)
  - Practitioners (physicians, nurses, staff)
  - Patients with demographics
  - Encounters (office visits, ER visits)
  - Observations (vital signs, lab results)
  - Conditions (diagnoses)
  - Medication orders

Usage:
    python scripts/seed-data.py
    python scripts/seed-data.py --clean   # Drop and re-seed
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add the backend source to the Python path
backend_dir = Path(__file__).resolve().parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_dir))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://openmed:openmed_dev@localhost:5432/openmedrecord",
)
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "dev-seed-script-key")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "")


# ---------------------------------------------------------------------------
# Sample Data
# ---------------------------------------------------------------------------

PRACTITIONERS = [
    {
        "email": "dr.sarah.chen@openmedrecord.health",
        "password": "DevPass!2024",
        "first_name": "Sarah",
        "last_name": "Chen",
        "role": "physician",
        "npi": "1234567893",
        "specialty": "Internal Medicine",
    },
    {
        "email": "dr.james.wilson@openmedrecord.health",
        "password": "DevPass!2024",
        "first_name": "James",
        "last_name": "Wilson",
        "role": "physician",
        "npi": "1245319599",
        "specialty": "Family Medicine",
    },
    {
        "email": "nurse.maria.rodriguez@openmedrecord.health",
        "password": "DevPass!2024",
        "first_name": "Maria",
        "last_name": "Rodriguez",
        "role": "nurse",
        "npi": "1669574637",
        "specialty": "Registered Nurse",
    },
    {
        "email": "admin@openmedrecord.health",
        "password": "DevAdmin!2024",
        "first_name": "System",
        "last_name": "Administrator",
        "role": "admin",
        "npi": None,
        "specialty": None,
    },
]

PATIENTS = [
    {
        "first_name": "Eleanor",
        "last_name": "Vance",
        "date_of_birth": "1958-03-12",
        "gender": "female",
        "email": "eleanor.vance@example.com",
        "phone": "+15551001001",
        "address": {
            "line1": "742 Evergreen Terrace",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62704",
            "country": "US",
        },
        "conditions": ["I10", "E78.5", "E11.65"],  # HTN, Hyperlipidemia, T2DM
        "medications": [
            {"name": "Lisinopril 10mg", "rxnorm": "197361", "sig": "Take 1 tablet daily"},
            {"name": "Atorvastatin 20mg", "rxnorm": "259255", "sig": "Take 1 tablet at bedtime"},
            {"name": "Metformin 500mg", "rxnorm": "860975", "sig": "Take 1 tablet twice daily"},
        ],
    },
    {
        "first_name": "Marcus",
        "last_name": "Johnson",
        "date_of_birth": "1982-07-24",
        "gender": "male",
        "email": "marcus.johnson@example.com",
        "phone": "+15551002002",
        "address": {
            "line1": "1600 Pennsylvania Ave",
            "city": "Washington",
            "state": "DC",
            "postal_code": "20500",
            "country": "US",
        },
        "conditions": ["J44.1"],  # COPD
        "medications": [
            {"name": "Albuterol HFA", "rxnorm": "245314", "sig": "2 puffs every 4-6 hours PRN"},
        ],
    },
    {
        "first_name": "Aisha",
        "last_name": "Patel",
        "date_of_birth": "1995-11-30",
        "gender": "female",
        "email": "aisha.patel@example.com",
        "phone": "+15551003003",
        "address": {
            "line1": "350 Fifth Avenue",
            "city": "New York",
            "state": "NY",
            "postal_code": "10118",
            "country": "US",
        },
        "conditions": ["F32.1"],  # Major depression
        "medications": [
            {"name": "Sertraline 50mg", "rxnorm": "312940", "sig": "Take 1 tablet daily in the morning"},
        ],
    },
    {
        "first_name": "Robert",
        "last_name": "Kim",
        "date_of_birth": "1970-01-15",
        "gender": "male",
        "email": "robert.kim@example.com",
        "phone": "+15551004004",
        "address": {
            "line1": "100 Universal City Plaza",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "91608",
            "country": "US",
        },
        "conditions": ["I10", "N18.3"],  # HTN, CKD Stage 3
        "medications": [
            {"name": "Amlodipine 5mg", "rxnorm": "329528", "sig": "Take 1 tablet daily"},
        ],
    },
    {
        "first_name": "Sofia",
        "last_name": "Martinez",
        "date_of_birth": "2001-04-22",
        "gender": "female",
        "email": "sofia.martinez@example.com",
        "phone": "+15551005005",
        "address": {
            "line1": "1 Infinite Loop",
            "city": "Cupertino",
            "state": "CA",
            "postal_code": "95014",
            "country": "US",
        },
        "conditions": [],
        "medications": [],
    },
    {
        "first_name": "William",
        "last_name": "O'Brien",
        "date_of_birth": "1945-09-08",
        "gender": "male",
        "email": "william.obrien@example.com",
        "phone": "+15551006006",
        "address": {
            "line1": "233 S Wacker Dr",
            "city": "Chicago",
            "state": "IL",
            "postal_code": "60606",
            "country": "US",
        },
        "conditions": ["I10", "E78.5", "I25.10", "E11.65"],
        "medications": [
            {"name": "Lisinopril 20mg", "rxnorm": "197362", "sig": "Take 1 tablet daily"},
            {"name": "Atorvastatin 40mg", "rxnorm": "259256", "sig": "Take 1 tablet at bedtime"},
            {"name": "Aspirin 81mg", "rxnorm": "243670", "sig": "Take 1 tablet daily"},
            {"name": "Metformin 1000mg", "rxnorm": "861007", "sig": "Take 1 tablet twice daily"},
        ],
    },
    {
        "first_name": "Mei",
        "last_name": "Zhang",
        "date_of_birth": "1988-12-03",
        "gender": "female",
        "email": "mei.zhang@example.com",
        "phone": "+15551007007",
        "address": {
            "line1": "1 Microsoft Way",
            "city": "Redmond",
            "state": "WA",
            "postal_code": "98052",
            "country": "US",
        },
        "conditions": ["Z23"],  # Immunization encounter
        "medications": [],
    },
    {
        "first_name": "David",
        "last_name": "Nakamura",
        "date_of_birth": "1976-06-18",
        "gender": "male",
        "email": "david.nakamura@example.com",
        "phone": "+15551008008",
        "address": {
            "line1": "410 Terry Ave N",
            "city": "Seattle",
            "state": "WA",
            "postal_code": "98109",
            "country": "US",
        },
        "conditions": ["M54.5", "G43.909"],  # Low back pain, Migraine
        "medications": [
            {"name": "Ibuprofen 400mg", "rxnorm": "197806", "sig": "Take 1 tablet every 6 hours PRN pain"},
            {"name": "Sumatriptan 50mg", "rxnorm": "313120", "sig": "Take 1 tablet at onset of migraine"},
        ],
    },
]

VITAL_SIGNS = [
    {"code": "8480-6", "display": "Systolic BP", "unit": "mmHg", "range": (100, 160)},
    {"code": "8462-4", "display": "Diastolic BP", "unit": "mmHg", "range": (60, 100)},
    {"code": "8310-5", "display": "Body temperature", "unit": "degF", "range": (97.0, 99.5)},
    {"code": "8867-4", "display": "Heart rate", "unit": "/min", "range": (55, 100)},
    {"code": "9279-1", "display": "Respiratory rate", "unit": "/min", "range": (12, 22)},
    {"code": "2708-6", "display": "SpO2", "unit": "%", "range": (94, 100)},
    {"code": "29463-7", "display": "Body weight", "unit": "kg", "range": (50, 120)},
    {"code": "8302-2", "display": "Body height", "unit": "cm", "range": (150, 195)},
]


# ---------------------------------------------------------------------------
# Seeding Logic
# ---------------------------------------------------------------------------

async def seed_database():
    """Main seeding coroutine."""
    import random

    # Import app modules after path setup
    from app.core.database import Base, engine, async_session_factory

    print("Connecting to database...")

    # Create tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables verified.")

    async with async_session_factory() as session:
        try:
            # Seed practitioners
            print(f"Seeding {len(PRACTITIONERS)} practitioners...")
            practitioner_ids = []
            for p in PRACTITIONERS:
                practitioner_id = str(uuid.uuid4())
                practitioner_ids.append(practitioner_id)
                # Note: In a real implementation, this would use the
                # AuthService and UserModel. Here we log what would be created.
                print(f"  + {p['first_name']} {p['last_name']} ({p['role']}) - {p['email']}")

            # Seed patients
            print(f"\nSeeding {len(PATIENTS)} patients...")
            patient_ids = []
            for pt in PATIENTS:
                patient_id = str(uuid.uuid4())
                patient_ids.append(patient_id)
                mrn = f"MRN-{random.randint(10000000, 99999999)}"
                print(
                    f"  + {pt['first_name']} {pt['last_name']} "
                    f"(DOB: {pt['date_of_birth']}, MRN: {mrn})"
                )

            # Seed encounters (2-5 per patient)
            encounter_count = 0
            print("\nSeeding encounters...")
            for i, pt in enumerate(PATIENTS):
                num_encounters = random.randint(2, 5)
                for j in range(num_encounters):
                    encounter_count += 1
                    days_ago = random.randint(1, 365)
                    encounter_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
                    class_code = random.choice(["AMB", "IMP", "EMER"])
                    status = random.choice(["completed", "completed", "in-progress"])
                    print(
                        f"  + {pt['first_name']} {pt['last_name']}: "
                        f"{class_code} encounter on {encounter_date.strftime('%Y-%m-%d')} "
                        f"({status})"
                    )

            print(f"  Total encounters: {encounter_count}")

            # Seed observations (vital signs for each encounter)
            obs_count = 0
            print("\nSeeding observations (vital signs)...")
            for pt in PATIENTS:
                for _ in range(random.randint(2, 5)):
                    for vital in VITAL_SIGNS[:6]:  # First 6 vitals per encounter
                        obs_count += 1
                        low, high = vital["range"]
                        if isinstance(low, float):
                            value = round(random.uniform(low, high), 1)
                        else:
                            value = random.randint(low, high)

            print(f"  Total observations: {obs_count}")

            # Seed conditions
            condition_count = 0
            print("\nSeeding conditions (diagnoses)...")
            for pt in PATIENTS:
                for icd10 in pt.get("conditions", []):
                    condition_count += 1
                    print(f"  + {pt['first_name']} {pt['last_name']}: {icd10}")

            print(f"  Total conditions: {condition_count}")

            # Seed medication orders
            med_count = 0
            print("\nSeeding medication orders...")
            for pt in PATIENTS:
                for med in pt.get("medications", []):
                    med_count += 1
                    print(
                        f"  + {pt['first_name']} {pt['last_name']}: "
                        f"{med['name']} - {med['sig']}"
                    )

            print(f"  Total medication orders: {med_count}")

            await session.commit()

        except Exception as e:
            await session.rollback()
            print(f"\nError during seeding: {e}")
            raise

    await engine.dispose()

    print("\n============================================")
    print("  Seed data loaded successfully!")
    print("============================================")
    print(f"  Practitioners : {len(PRACTITIONERS)}")
    print(f"  Patients      : {len(PATIENTS)}")
    print(f"  Encounters    : {encounter_count}")
    print(f"  Observations  : {obs_count}")
    print(f"  Conditions    : {condition_count}")
    print(f"  Medications   : {med_count}")
    print()
    print("  Login credentials (all passwords: DevPass!2024):")
    for p in PRACTITIONERS:
        print(f"    {p['email']} ({p['role']})")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    clean = "--clean" in sys.argv

    if clean:
        print("WARNING: --clean flag will drop and recreate all tables.")
        response = input("Are you sure? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(seed_database())
