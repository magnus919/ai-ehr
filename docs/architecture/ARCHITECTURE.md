# OpenMedRecord -- Architectural Design Document

| Field            | Value                                      |
|------------------|--------------------------------------------|
| **Project**      | OpenMedRecord                              |
| **Type**         | Enterprise Electronic Health Record System |
| **License**      | Open Source (Apache 2.0)                   |
| **Version**      | 1.1.0                                      |
| **Status**       | Draft                                      |
| **Change Note**  | v1.1.0 -- Incorporated findings from tech lead, architecture, and security reviews. Added CDS, reporting, consent, and HL7v2 services. Expanded data model. Added ADRs 006-008. Reconciled cross-document inconsistencies. |
| **Last Updated** | 2026-02-11                                 |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Views](#2-architecture-views)
   - 2.1 [Logical Architecture](#21-logical-architecture)
   - 2.2 [Deployment Architecture (AWS)](#22-deployment-architecture-aws)
   - 2.3 [Data Architecture](#23-data-architecture)
   - 2.4 [Security Architecture](#24-security-architecture)
   - 2.5 [Integration Architecture](#25-integration-architecture)
3. [API Design](#3-api-design)
4. [Data Model](#4-data-model)
5. [Security Controls](#5-security-controls)
6. [Infrastructure](#6-infrastructure)
7. [Disaster Recovery](#7-disaster-recovery)
8. [Technology Decisions (ADRs)](#8-technology-decisions-adrs)

---

## 1. System Overview

OpenMedRecord is an open-source, cloud-native Electronic Health Record (EHR)
platform designed for enterprise healthcare organizations. It provides a
standards-compliant (FHIR R4, HL7v2), HIPAA-ready foundation for managing
patient health information across ambulatory, inpatient, and specialty-care
settings.

### 1.1 High-Level Architecture

```
                          +---------------------+
                          |    End Users         |
                          | (Clinicians, Staff,  |
                          |  Patients, Admins)   |
                          +----------+----------+
                                     |
                                     | HTTPS
                                     v
                          +---------------------+
                          |  AWS CloudFront CDN  |
                          |  (React SPA + WAF)   |
                          +----------+----------+
                                     |
                          +----------+----------+
                          |  Application Load    |
                          |  Balancer (ALB)      |
                          +----------+----------+
                                     |
                    +----------------+----------------+
                    |                |                 |
               +----v----+    +-----v-----+    +------v------+
               |  Auth   |    |   FHIR    |    | API Gateway |
               | Service |    |  Gateway  |    |  (FastAPI)  |
               +---------+    +-----------+    +------+------+
                                                      |
              +----------+----------+----------+------+------+
              |          |          |          |             |
         +----v---+ +----v----+ +--v-----+ +-v--------+ +--v----------+
         |Patient | |Clinical | | Order  | |Scheduling| |Notification |
         |Service | |Service  | |Service | | Service  | |  Service    |
         +----+---+ +----+---+ +---+----+ +----+-----+ +------+------+
              |          |         |            |               |
              +----------+---------+------------+-------+-------+
                                   |                    |
                         +---------v--------+  +--------v--------+
                         | Aurora PostgreSQL |  |    DynamoDB     |
                         |   (Multi-AZ)     |  | (Sessions/Audit)|
                         +------------------+  +-----------------+
                                   |
                         +---------v--------+
                         | ElastiCache Redis |
                         |    (Caching)      |
                         +------------------+

         +-------------------+          +-------------------+
         |   EventBridge     |<-------->|       SQS         |
         | (Event Bus)       |          |  (Task Queues)    |
         +-------------------+          +-------------------+

         +-------------------+          +-------------------+
         | HAPI FHIR Server  |          |  AWS HealthLake   |
         | (ECS / Optional)  |          |   (Optional)      |
         +-------------------+          +-------------------+
```

### 1.2 Technology Stack Summary

| Layer              | Technology                                      |
|--------------------|-------------------------------------------------|
| Frontend           | React 18, TypeScript 5, Vite, TanStack Query    |
| Backend Framework  | Python 3.12, FastAPI 0.110+, Pydantic v2         |
| Compute            | AWS ECS Fargate (serverless containers)           |
| Primary Database   | Amazon Aurora PostgreSQL 16 (Multi-AZ)            |
| Session/Audit DB   | Amazon DynamoDB (on-demand capacity)               |
| Caching            | Amazon ElastiCache for Redis 7 (cluster mode)     |
| FHIR Server        | HAPI FHIR R4 on ECS or AWS HealthLake             |
| Messaging          | Amazon EventBridge + Amazon SQS                   |
| CDN / Frontend     | Amazon CloudFront + S3                             |
| Auth               | Amazon Cognito + custom OAuth2/OIDC service        |
| Secrets            | AWS Secrets Manager                                |
| Encryption         | AWS KMS (customer-managed keys)                    |
| Web Security       | AWS WAF v2                                         |
| IaC                | AWS CDK (TypeScript)                               |
| CI/CD              | GitHub Actions + AWS CodePipeline                  |
| Monitoring         | CloudWatch, X-Ray, OpenTelemetry                   |
| Container Registry | Amazon ECR                                         |

### 1.3 Design Principles

1. **Security-First** -- Every design decision is evaluated through the lens of
   HIPAA compliance, data confidentiality, and least-privilege access. PHI is
   encrypted at rest and in transit with no exceptions.

2. **FHIR-First** -- The system uses a relational data model optimized for
   clinical workflows with a FHIR R4 facade for interoperability. Internal
   services use domain-specific models; FHIR translation occurs at the API
   boundary.

3. **Event-Driven** -- Services communicate asynchronously through events
   wherever possible, reducing temporal coupling and improving resilience.
   Synchronous calls are reserved for user-facing request/response flows.

4. **Multi-Tenant** -- A single deployment serves multiple healthcare
   organizations with strong data isolation using a schema-per-tenant bridge
   model in Aurora PostgreSQL.

5. **Cloud-Native** -- The system leverages managed AWS services to minimize
   operational burden. Containers are serverless (Fargate), databases are
   managed (Aurora, DynamoDB), and infrastructure is codified (CDK).

6. **Open Standards** -- The platform prioritizes open standards (FHIR, OAuth2,
   OpenID Connect, SMART on FHIR) to maximize interoperability and avoid
   vendor lock-in.

7. **Observable** -- Every service emits structured logs, metrics, and
   distributed traces. The system supports full audit reconstruction for any
   PHI access event.

---

## 2. Architecture Views

### 2.1 Logical Architecture

#### 2.1.1 Service Decomposition

OpenMedRecord follows a domain-driven microservices architecture. Each service
owns its bounded context, exposes a well-defined API, and manages its own data
partition within the shared Aurora cluster.

```
+------------------------------------------------------------------+
|                     API Gateway / ALB                              |
+------------------------------------------------------------------+
        |          |          |          |         |          |
   +----v---+ +----v----+ +--v-----+ +-v------+ +v-------+ +v---------+
   |  auth  | |patient  | |clinical| | order  | |schedule| |  audit   |
   |service | |service  | |service | |service | |service | | service  |
   |        | |         | |        | |        | |        | |          |
   |OAuth2  | |Demogr.  | |Notes,  | |Lab,Rx, | |Appts,  | |Immutable |
   |OIDC    | |Identity | |Dx,Vitals| |Imaging | |Calendar| |Event Log |
   |Tokens  | |Search   | |Allergy | |eRx     | |Rooms   | |PHI Audit |
   +--------+ +---------+ +--------+ +--------+ +--------+ +----------+
        |          |          |          |         |          |
   +----v---+ +----v---+ +---v-----+ +-v------+ +v--------+ |
   | fhir   | |notif.  | |  cds   | |report. | |consent  | |
   |gateway | |service | |service | |service | |service  | |
   |        | |        | |        | |        | |         | |
   |R4 API  | |Email,  | |CDS     | |eCQM,   | |Consent  | |
   |Mapping | |SMS,Push| |Hooks,  | |Dashb., | |Eval,    | |
   |        | |        | |Drug Ix | |Pop Hlth| |42CFR P2 | |
   +--------+ +--------+ +--------+ +--------+ +---------+ |
        |                                                    |
        +-- All services publish events to EventBridge ----->+
```

**Service Catalog:**

| Service                | Responsibility                                           | Port  |
|------------------------|----------------------------------------------------------|-------|
| `auth-service`         | OAuth2/OIDC provider, token issuance, MFA, SMART launch  | 8000  |
| `patient-service`      | Patient demographics, identity matching, master index     | 8001  |
| `clinical-service`     | Clinical documents, observations, conditions, allergies   | 8002  |
| `order-service`        | Lab orders, medication orders, imaging orders, eRx        | 8003  |
| `scheduling-service`   | Appointment management, resource scheduling, calendars    | 8004  |
| `audit-service`        | Immutable audit log ingestion, compliance reporting       | 8005  |
| `fhir-gateway`         | FHIR R4 facade, resource mapping, bulk data export        | 8006  |
| `notification-service` | Multi-channel notifications (email, SMS, push, in-app)    | 8007  |
| `cds-service`          | Clinical decision support, drug interaction checking, CDS Hooks, clinical rules engine | 8008  |
| `reporting-service`    | eCQM calculation (CQL), operational dashboards, population health analytics, ad hoc reports | 8009  |
| `hl7v2-engine`         | HL7v2 message parsing, routing, transformation (ADT, ORM, ORU, DFT). MLLP/TLS listener | 2575  |
| `consent-service`      | FHIR Consent resource management, consent evaluation at data access, 42 CFR Part 2 enforcement | 8010  |

#### 2.1.2 Domain Model

```
                        +----------------+
                        |   Tenant       |
                        | (Organization) |
                        +-------+--------+
                                |
                  +-------------+-------------+
                  |                           |
           +------v------+           +--------v-------+
           |    User      |           |   Location     |
           | (Clinician,  |           | (Facility,     |
           |  Staff,      |           |  Department)   |
           |  Admin)      |           +--------+-------+
           +------+-------+                    |
                  |                             |
           +------v-------+                    |
           |    Role       |                    |
           | (RBAC + ABAC) |                    |
           +--------------+                    |
                                               |
           +---------------+           +-------v--------+
           |   Patient     |<--------->|   Encounter    |
           | (Demographics,|           | (Visit, Stay,  |
           |  Identifiers) |           |  Episode)      |
           +-------+-------+           +-------+--------+
                   |                            |
        +----------+----------+      +----------+----------+
        |          |          |      |          |          |
   +----v---+ +---v----+ +---v--+ +-v------+ +v-------+ +v---------+
   |Allergy | |Condition| |Obs.  | | Order  | |Schedule| |  Note    |
   |Intol.  | |(Dx/Prob)| |(Vital| |(Lab,Rx | |(Appt)  | |(Clinical |
   |        | |         | | Sign)| | Image) | |        | | Document)|
   +--------+ +--------+ +------+ +--------+ +--------+ +----------+
```

#### 2.1.3 Service Interactions

Services communicate through two patterns:

**Synchronous (Request/Response)** -- Used for user-facing API calls where
immediate response is required. Services call each other through internal
ALB-routed HTTP endpoints using service discovery.

**Asynchronous (Event-Driven)** -- Used for cross-cutting concerns, eventual
consistency, and side effects. Services publish domain events to EventBridge;
interested services subscribe through SQS queues.

```
  User Request Flow (Synchronous):

  Client --> ALB --> patient-service --> Aurora PostgreSQL
                                    --> ElastiCache (cache check)
                                    --> Response to Client

  Event Flow (Asynchronous):

  clinical-service --[ObservationCreated]--> EventBridge
       |                                        |
       |                            +-----------+-----------+
       |                            |                       |
       |                    +-------v-------+       +-------v-------+
       |                    | SQS: audit    |       | SQS: notify   |
       |                    +-------+-------+       +-------+-------+
       |                            |                       |
       |                    +-------v-------+       +-------v-------+
       |                    | audit-service |       | notification  |
       |                    | (log event)   |       | service       |
       |                    +---------------+       | (alert if     |
       |                                            |  critical)    |
       |                                            +---------------+
```

**Key Event Types:**

| Event                      | Publisher          | Subscribers                        |
|----------------------------|--------------------|------------------------------------|
| `patient.created`          | patient-service    | audit-service, fhir-gateway         |
| `patient.updated`          | patient-service    | audit-service, fhir-gateway, notif. |
| `encounter.started`        | clinical-service   | audit-service, scheduling-service    |
| `encounter.completed`      | clinical-service   | audit-service, order-service         |
| `observation.created`      | clinical-service   | audit-service, notification-service  |
| `order.placed`             | order-service      | audit-service, notification-service  |
| `order.resulted`           | order-service      | clinical-service, notification-svc   |
| `medication.prescribed`    | order-service      | audit-service, notification-service  |
| `appointment.booked`       | scheduling-service | audit-service, notification-service  |
| `appointment.cancelled`    | scheduling-service | audit-service, notification-service  |
| `user.authenticated`       | auth-service       | audit-service                        |
| `phi.accessed`             | all services       | audit-service                        |

---

### 2.2 Deployment Architecture (AWS)

#### 2.2.1 VPC Design

The VPC spans three Availability Zones for high availability. Each AZ contains
three subnet tiers.

```
+=========================================================================+
|                          VPC: 10.0.0.0/16                               |
|                                                                         |
|  +-------------------+  +-------------------+  +-------------------+    |
|  |   AZ-a (us-east-1a)|  |   AZ-b (us-east-1b)|  |   AZ-c (us-east-1c)|   |
|  |                   |  |                   |  |                   |    |
|  | +---------------+ |  | +---------------+ |  | +---------------+ |   |
|  | | Public Subnet | |  | | Public Subnet | |  | | Public Subnet | |   |
|  | | 10.0.1.0/24   | |  | | 10.0.2.0/24   | |  | | 10.0.3.0/24   | |   |
|  | | - NAT Gateway | |  | | - NAT Gateway | |  | | - NAT Gateway | |   |
|  | | - ALB nodes   | |  | | - ALB nodes   | |  | | - ALB nodes   | |   |
|  | +---------------+ |  | +---------------+ |  | +---------------+ |   |
|  |                   |  |                   |  |                   |    |
|  | +---------------+ |  | +---------------+ |  | +---------------+ |   |
|  | |Private Subnet | |  | |Private Subnet | |  | |Private Subnet | |   |
|  | | 10.0.11.0/24  | |  | | 10.0.12.0/24  | |  | | 10.0.13.0/24  | |   |
|  | | - ECS Fargate | |  | | - ECS Fargate | |  | | - ECS Fargate | |   |
|  | |   Tasks       | |  | |   Tasks       | |  | |   Tasks       | |   |
|  | | - HAPI FHIR   | |  | | - HAPI FHIR   | |  | | - HAPI FHIR   | |   |
|  | +---------------+ |  | +---------------+ |  | +---------------+ |   |
|  |                   |  |                   |  |                   |    |
|  | +---------------+ |  | +---------------+ |  | +---------------+ |   |
|  | | Data Subnet   | |  | | Data Subnet   | |  | | Data Subnet   | |   |
|  | | 10.0.21.0/24  | |  | | 10.0.22.0/24  | |  | | 10.0.23.0/24  | |   |
|  | | - Aurora PG    | |  | | - Aurora PG    | |  | | - Aurora PG    | |   |
|  | |   instances   | |  | |   (replica)   | |  | |   (replica)   | |   |
|  | | - ElastiCache | |  | | - ElastiCache | |  | | - ElastiCache | |   |
|  | |   nodes       | |  | |   nodes       | |  | |   nodes       | |   |
|  | +---------------+ |  | +---------------+ |  | +---------------+ |   |
|  +-------------------+  +-------------------+  +-------------------+    |
|                                                                         |
|  VPC Endpoints: S3, DynamoDB, ECR, CloudWatch, Secrets Manager, KMS,    |
|                 SQS, EventBridge, STS                                   |
+=========================================================================+
```

#### 2.2.2 Full AWS Deployment Diagram

```
                            +---------------------------+
                            |      Route 53 DNS         |
                            |  openmedrecord.health     |
                            +------------+--------------+
                                         |
                            +------------v--------------+
                            |    AWS WAF v2             |
                            |  (OWASP rules, rate       |
                            |   limiting, geo-blocking) |
                            +------------+--------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
          +----------v----------+               +------------v-----------+
          |   CloudFront CDN    |               |   CloudFront CDN       |
          |  (SPA Distribution) |               |  (API Distribution)    |
          +----------+----------+               +------------+-----------+
                     |                                       |
          +----------v----------+               +------------v-----------+
          |   S3 Bucket         |               | Application Load       |
          |  (React SPA         |               | Balancer (ALB)         |
          |   static assets)    |               | - SSL/TLS termination  |
          +---------------------+               | - Path-based routing   |
                                                +-----+-----+-----+-----+
                                                      |     |     |
                                    +-----------------+     |     +--------+
                                    |                       |              |
                              +-----v------+         +-----v------+ +-----v------+
                              | Target     |         | Target     | | Target     |
                              | Group:     |         | Group:     | | Group:     |
                              | /api/v1/*  |         | /auth/*    | | /fhir/*    |
                              +-----+------+         +-----+------+ +-----+------+
                                    |                       |              |
                         +----------v----------+    +-------v---+  +------v-------+
                         | ECS Fargate Cluster |    | auth      |  | fhir-gateway |
                         |                     |    | service   |  | service      |
                         | +-------+ +-------+ |    +-----------+  +--------------+
                         | |patient| |clinic.| |
                         | |svc    | |svc    | |    +----------------------------------+
                         | +-------+ +-------+ |    | Amazon Cognito User Pool         |
                         | +-------+ +-------+ |    | - User directory                 |
                         | |order  | |sched. | |    | - MFA                            |
                         | |svc    | |svc    | |    | - OAuth2/OIDC endpoints          |
                         | +-------+ +-------+ |    +----------------------------------+
                         | +-------+ +-------+ |
                         | |audit  | |notif. | |
                         | |svc    | |svc    | |
                         | +-------+ +-------+ |
                         +----------+----------+
                                    |
              +---------------------+---------------------+
              |                     |                      |
   +----------v---------+ +--------v---------+ +----------v----------+
   | Aurora PostgreSQL   | |  DynamoDB        | |  ElastiCache Redis  |
   | Cluster             | |                  | |  Cluster            |
   | - Writer (AZ-a)     | | - sessions table | | - 3 nodes           |
   | - Reader (AZ-b)     | | - audit_events   | | - cluster mode      |
   | - Reader (AZ-c)     | |   table          | | - encryption at     |
   | - Encrypted (KMS)   | | - Encrypted      | |   rest + transit    |
   +---------------------+ +------------------+ +---------------------+

   +---------------------+ +------------------+ +---------------------+
   | Amazon EventBridge  | | Amazon SQS       | | AWS Secrets Manager |
   | - default bus       | | - audit-queue    | | - DB credentials    |
   | - openmedrecord bus | | - notify-queue   | | - API keys          |
   |                     | | - order-queue    | | - JWT signing keys  |
   |                     | | - DLQ per queue  | |                     |
   +---------------------+ +------------------+ +---------------------+

   +---------------------+ +------------------+ +---------------------+
   | AWS KMS             | | Amazon ECR       | | CloudWatch + X-Ray  |
   | - CMK: data-at-rest | | - Service images | | - Logs, Metrics     |
   | - CMK: envelope     | | - HAPI FHIR img  | | - Distributed traces|
   +---------------------+ +------------------+ +---------------------+
```

#### 2.2.3 Network Security

- **Public Subnets** -- Only NAT Gateways and ALB nodes. No direct-access
  compute resources.
- **Private Subnets** -- All ECS Fargate tasks. Outbound internet via NAT
  Gateway. Inbound only from ALB security group.
- **Data Subnets** -- Aurora and ElastiCache. No internet route. Inbound only
  from private subnet security groups.
- **VPC Endpoints** -- Interface and gateway endpoints for AWS services to keep
  traffic off the public internet: S3 (gateway), DynamoDB (gateway), ECR API
  and Docker (interface), CloudWatch Logs (interface), Secrets Manager
  (interface), KMS (interface), SQS (interface), EventBridge (interface), STS
  (interface).

**Security Group Matrix:**

| Source SG               | Destination SG     | Port      | Protocol | Purpose                       |
|-------------------------|--------------------|-----------|----------|-------------------------------|
| ALB-SG                  | ECS-SG             | 8000-8010 | TCP      | ALB to services               |
| ECS-SG                  | Aurora-SG          | 5432      | TCP      | Services to database          |
| ECS-SG                  | Redis-SG           | 6379      | TCP      | Services to cache             |
| ECS-SG                  | VPC-Endpoints-SG   | 443       | TCP      | Services to AWS APIs          |
| CloudFront-PL           | ALB-SG             | 443       | TCP      | CDN to ALB                    |
| VPN/DirectConnect       | NLB-SG             | 2575      | TCP      | HL7v2 MLLP ingress            |

> **Note:** Default deny on all security groups. Only explicitly listed rules
> are permitted. No security group allows `0.0.0.0/0` ingress.

---

### 2.3 Data Architecture

#### 2.3.1 Multi-Tenancy Strategy: Schema-per-Tenant Bridge Model

OpenMedRecord uses a schema-per-tenant model in Aurora PostgreSQL. Each tenant
organization receives its own PostgreSQL schema within a shared database cluster.
A `shared` schema holds cross-tenant metadata (tenant registry, global
configuration).

```
Aurora PostgreSQL Cluster
+---------------------------------------------------------------+
| Database: openmedrecord                                       |
|                                                               |
| +------------------+  +------------------+  +---------------+ |
| | Schema: shared   |  | Schema: tenant_1 |  | Schema: t_N   | |
| |                  |  |                  |  |               | |
| | - tenants        |  | - patients       |  | - patients    | |
| | - global_config  |  | - encounters     |  | - encounters  | |
| | - tenant_users   |  | - observations   |  | ...           | |
| |   (bridge table) |  | - conditions     |  |               | |
| |                  |  | - medications    |  |               | |
| |                  |  | - orders         |  |               | |
| |                  |  | - audit_logs     |  |               | |
| |                  |  | - users          |  |               | |
| +------------------+  +------------------+  +---------------+ |
+---------------------------------------------------------------+
```

**Bridge Model Details:**

- The `shared.tenant_users` table maps Cognito user identities to one or more
  tenant schemas, enabling clinicians who work across organizations to switch
  context.
- Each service sets `search_path` to the active tenant's schema on every
  database connection, enforced by middleware.
- Row-level security (RLS) provides an additional layer of isolation as a
  defense-in-depth measure.

#### 2.3.2 Core Database Schema

```
  +-------------------+       +--------------------+       +-------------------+
  |    patients       |       |    encounters      |       |   observations    |
  |-------------------|       |--------------------|       |-------------------|
  | id           UUID |PK     | id           UUID  |PK     | id          UUID  |PK
  | mrn       VARCHAR |UQ     | patient_id   UUID  |FK---->| encounter_id UUID |FK
  | fhir_id  VARCHAR  |UQ     | type       VARCHAR |       | patient_id  UUID  |FK
  | given_name VARCHAR|       | status     VARCHAR |       | code       VARCHAR|
  | family_name VARCHAR|      | class      VARCHAR |       | code_system VARCHAR|
  | birth_date  DATE  |       | period_start TSTZ  |       | value_type VARCHAR|
  | gender    VARCHAR |       | period_end   TSTZ  |       | value_string VARCHAR|
  | address    JSONB  |       | location_id  UUID  |FK     | value_numeric DEC |
  | telecom    JSONB  |       | practitioner_id UUID|FK    | value_unit VARCHAR|
  | identifiers JSONB |       | reason_code  JSONB |       | effective_dt TSTZ |
  | active    BOOLEAN |       | diagnosis    JSONB |       | issued_dt   TSTZ  |
  | created_at  TSTZ  |       | created_at   TSTZ  |       | status    VARCHAR |
  | updated_at  TSTZ  |       | updated_at   TSTZ  |       | created_at  TSTZ  |
  | created_by  UUID  |FK     | created_by   UUID  |FK     | created_by  UUID  |FK
  +-------------------+       +--------------------+       +-------------------+
           |                           |
           |                           |
  +--------v----------+       +--------v-----------+       +-------------------+
  |   conditions      |       |    medications     |       |     orders        |
  |-------------------|       |--------------------|       |-------------------|
  | id           UUID |PK     | id           UUID  |PK     | id          UUID  |PK
  | patient_id   UUID |FK     | patient_id   UUID  |FK     | patient_id  UUID  |FK
  | encounter_id UUID |FK     | encounter_id UUID  |FK     | encounter_id UUID |FK
  | code       VARCHAR|       | code       VARCHAR |       | order_type VARCHAR|
  | code_system VARCHAR|      | code_system VARCHAR|       | code       VARCHAR|
  | display    VARCHAR|       | display    VARCHAR |       | code_system VARCHAR|
  | clinical_status VARCHAR|  | status     VARCHAR |       | status    VARCHAR |
  | verification VARCHAR|     | dosage      JSONB  |       | priority  VARCHAR |
  | severity  VARCHAR |       | route      VARCHAR |       | requester_id UUID |FK
  | onset_date  TSTZ  |       | frequency  VARCHAR |       | performer_id UUID |FK
  | abatement_dt TSTZ |       | start_date  TSTZ   |       | reason     JSONB  |
  | recorded_dt  TSTZ |       | end_date    TSTZ   |       | specimen    JSONB |
  | created_at   TSTZ |       | prescriber_id UUID |FK     | result      JSONB |
  | created_by   UUID |FK     | created_at   TSTZ  |       | ordered_dt  TSTZ  |
  +-------------------+       | created_by   UUID  |FK     | completed_dt TSTZ |
                              +--------------------+       | created_at   TSTZ |
                                                           | created_by   UUID |FK
  +-------------------+       +--------------------+       +-------------------+
  |     users         |       |   audit_logs       |
  |-------------------|       |--------------------|
  | id           UUID |PK     | id           UUID  |PK
  | cognito_sub VARCHAR|UQ    | timestamp     TSTZ |
  | email      VARCHAR|UQ     | actor_id     UUID  |FK
  | given_name VARCHAR|       | actor_role  VARCHAR|
  | family_name VARCHAR|      | action     VARCHAR |
  | role_id      UUID |FK     | resource_type VARCHAR|
  | specialty  VARCHAR|       | resource_id  UUID  |
  | npi        VARCHAR|       | detail       JSONB |
  | active    BOOLEAN |       | source_ip  VARCHAR |
  | mfa_enabled BOOL  |       | user_agent VARCHAR |
  | last_login  TSTZ  |       | tenant_id  VARCHAR |
  | created_at  TSTZ  |       | outcome   VARCHAR  |
  | updated_at  TSTZ  |       +--------------------+
  +-------------------+
```

#### 2.3.3 Data Flow Diagram

```
  Clinical User Action                 System Data Flow
  =====================               ==================

  1. Clinician records        HTTP POST /api/v1/observations
     a vital sign                       |
                                        v
                               +------------------+
                               | clinical-service |
                               +--------+---------+
                                        |
                          +-------------+-------------+
                          |                           |
                   +------v------+           +--------v--------+
                   | Validate    |           | Check cache for |
                   | via Pydantic|           | patient context |
                   | + FHIR R4   |           | (ElastiCache)   |
                   +------+------+           +-----------------+
                          |
                   +------v------+
                   | Write to    |
                   | Aurora PG   |
                   | (tenant     |
                   |  schema)    |
                   +------+------+
                          |
                   +------v------+
                   | Invalidate  |
                   | cache keys  |
                   +------+------+
                          |
                   +------v------+
                   | Publish     |
                   | event to    |
                   | EventBridge |
                   +------+------+
                          |
              +-----------+-----------+
              |                       |
       +------v------+        +------v------+
       | audit-svc   |        | notif-svc   |
       | writes to   |        | checks CDS  |
       | DynamoDB +  |        | rules, sends|
       | Aurora      |        | alerts      |
       +-------------+        +-------------+
```

#### 2.3.3a Redis Cache PHI Policy

ElastiCache Redis is used for performance optimization but carries additional
risk as an in-memory data store. The following policies apply:

**Permitted Cache Contents:**

- Patient demographics: name, MRN, date of birth, active status
- Active medication list (code, display, status -- no prescriber notes)
- Allergy list (code, display, criticality, clinical status)
- Session tokens and CSRF tokens
- FHIR CapabilityStatement and metadata responses
- Rate limiting counters

**Prohibited Cache Contents (MUST NOT be cached):**

- Social Security Numbers (SSN)
- Substance abuse data (42 CFR Part 2 protected)
- Psychotherapy notes
- HIV/AIDS status (where state law restricts)
- Genomic data
- Full clinical note content

**Cache Security Controls:**

- All cache entries containing PHI have a maximum TTL of 15 minutes.
- Redis `MONITOR` and `DEBUG` commands are disabled in production via
  `rename-command` configuration.
- Redis AUTH is required; credentials rotated per secret rotation policy.
- Encryption at rest (KMS) and in transit (TLS) are mandatory.
- Cache keys use tenant-scoped prefixes (`{tenant_id}:{resource}:{id}`)
  to prevent cross-tenant data leakage.

#### 2.3.4 FHIR Resource Mapping

Internal database tables map to FHIR R4 resources. The `fhir-gateway` service
handles bidirectional transformation.

| Internal Table   | FHIR R4 Resource       | Notes                           |
|------------------|------------------------|---------------------------------|
| `patients`       | `Patient`              | Direct 1:1 mapping              |
| `encounters`     | `Encounter`            | Direct 1:1 mapping              |
| `observations`   | `Observation`          | Vitals, lab results, assessments|
| `conditions`     | `Condition`            | Diagnoses, problem list         |
| `medications`    | `MedicationRequest`    | Active prescriptions            |
| `medications`    | `MedicationStatement`  | Reported medications            |
| `orders`         | `ServiceRequest`       | Lab, imaging orders             |
| `orders`         | `DiagnosticReport`     | When results present            |
| `users`          | `Practitioner`         | Clinician identity              |
| `audit_logs`     | `AuditEvent`           | FHIR AuditEvent resource        |
| `encounters` + `conditions` | `EpisodeOfCare` | Aggregated view          |

---

### 2.4 Security Architecture

#### 2.4.1 Authentication Flow (OAuth2 / OIDC)

```
  +--------+                                +-------------+
  | User   |                                |  Cognito /  |
  | Browser|                                |  Auth Svc   |
  +---+----+                                +------+------+
      |                                            |
      |  1. GET /login                             |
      |  (redirect to auth)                        |
      |------------------------------------------->|
      |                                            |
      |  2. Login page                             |
      |  (username/password + MFA)                 |
      |<-------------------------------------------|
      |                                            |
      |  3. POST credentials                       |
      |------------------------------------------->|
      |                                            |
      |  4. MFA challenge (TOTP/SMS)               |
      |<-------------------------------------------|
      |                                            |
      |  5. MFA response                           |
      |------------------------------------------->|
      |                                            |
      |  6. Authorization code                     |
      |  (redirect to /callback)                   |
      |<-------------------------------------------|
      |                                            |
      |  7. Exchange code for tokens               |
      |     (via auth-service backend)             |
      |     - ID Token (identity claims)           |
      |     - Access Token (API authorization)     |
      |     - Refresh Token (session renewal)      |
      |                                            |
      |  8. Store access token in memory,          |
      |     refresh token in httpOnly cookie       |
      |                                            |
      |  9. API calls with Bearer token            |
      |--> ALB --> ECS Service                     |
      |           |                                |
      |           | Validate JWT signature         |
      |           | Check expiry, issuer, audience |
      |           | Extract tenant_id, user_id,    |
      |           |   roles, permissions           |
      |           |                                |
      |           | Set search_path to tenant      |
      |           | schema in DB connection        |
      |                                            |
```

**Token Specifications:**

| Token          | Lifetime | Storage            | Contents                        |
|----------------|----------|--------------------|---------------------------------|
| ID Token       | 1 hour   | JavaScript memory  | User identity claims            |
| Access Token   | 15 min   | JavaScript memory  | Roles, permissions, tenant_id   |
| Refresh Token  | 24 hours | httpOnly cookie    | Opaque, stored in DynamoDB      |
| Session Token  | 8 hours  | DynamoDB           | Server-side session state       |

#### 2.4.2 Authorization Model (RBAC + ABAC)

OpenMedRecord combines Role-Based Access Control (RBAC) with Attribute-Based
Access Control (ABAC) for fine-grained authorization.

**RBAC Roles:**

| Role               | Description                                          |
|--------------------|------------------------------------------------------|
| `system_admin`     | Full system access, tenant management                |
| `org_admin`        | Tenant-level administration, user management         |
| `physician`        | Full clinical read/write within care team            |
| `nurse`            | Clinical read/write, limited ordering                |
| `pharmacist`       | Medication review, order verification                |
| `lab_tech`         | Lab order processing, result entry                   |
| `scheduler`        | Appointment management, no clinical data             |
| `billing`          | Encounter and diagnosis read, no clinical notes      |
| `patient`          | Own records only (patient portal)                    |
| `read_only_audit`  | Audit log read access for compliance officers        |

**ABAC Attributes:**

```python
# Authorization policy pseudocode
def authorize(subject, action, resource, context):
    # RBAC check
    if action not in subject.role.permissions:
        return DENY

    # ABAC attribute checks
    if resource.tenant_id != subject.tenant_id:
        return DENY

    if resource.type == "clinical_note":
        if subject.role == "billing":
            return DENY
        if not is_care_team_member(subject, resource.patient_id):
            if not has_break_glass(context):
                return DENY
            else:
                log_break_glass_event(subject, resource, context)

    if context.ip_not_in_allowed_range(subject.ip_policy):
        return DENY

    if context.time_outside_schedule(subject.access_schedule):
        return DENY

    return ALLOW
```

**Break-Glass Procedure:**

In emergency situations, clinicians can invoke break-glass access to view
patient records outside their normal care team scope. This access:

1. Requires explicit user confirmation with documented reason.
2. Generates a high-priority audit event.
3. Triggers immediate notification to the privacy officer.
4. Is time-limited (60 minutes default, configurable maximum of 4 hours with
   security officer approval). Periodic re-authentication is required every
   30 minutes during break-glass sessions.
5. Is subject to post-hoc review.

#### 2.4.3 Encryption

**At Rest:**

| Data Store         | Encryption Method       | Key Management              |
|--------------------|-------------------------|-----------------------------|
| Aurora PostgreSQL  | AES-256, TDE            | AWS KMS CMK (auto-rotate)   |
| DynamoDB           | AES-256                 | AWS KMS CMK                 |
| ElastiCache Redis  | AES-256                 | AWS KMS CMK                 |
| S3 Buckets         | SSE-KMS (AES-256)       | AWS KMS CMK                 |
| EBS Volumes        | AES-256                 | AWS KMS CMK                 |
| Secrets Manager    | AES-256                 | AWS KMS CMK                 |

**In Transit:**

| Path                     | Protocol    | Minimum Version | Certificate           |
|--------------------------|-------------|------------------|-----------------------|
| Client to CloudFront     | TLS         | 1.2              | ACM public cert       |
| CloudFront to ALB        | TLS         | 1.2              | ACM public cert       |
| ALB to ECS tasks         | TLS         | 1.2              | ACM private cert      |
| ECS to Aurora            | TLS         | 1.2              | RDS CA cert           |
| ECS to ElastiCache       | TLS         | 1.2              | ElastiCache CA cert   |
| ECS to DynamoDB          | TLS         | 1.2              | AWS endpoint cert     |
| Inter-service (ECS-ECS)  | mTLS        | 1.3              | ACM Private CA        |

**Secret Rotation Cadences:**

| Secret Type             | Rotation Period | Mechanism                                  | Notes                                       |
|-------------------------|-----------------|--------------------------------------------|---------------------------------------------|
| Database credentials    | 90 days         | AWS Secrets Manager automatic rotation     | Lambda-based rotation function              |
| JWT signing keys        | Annual          | Manual rotation with 7-day overlap period  | Both old and new keys valid during overlap   |
| API partner keys        | Per-partner policy, max 1 year | Secrets Manager or partner portal | Expiry enforced; alerts at 30 days remaining |
| KMS CMK                 | Annual          | KMS automatic key rotation                 | Previous key versions retained for decrypt  |
| Application-level DEKs  | 90 days         | Application-managed envelope encryption    | Re-encryption of active data on rotation    |

#### 2.4.4 Audit Logging Pipeline

```
  +------------------+     +------------------+     +------------------+
  | Application      |     |   EventBridge    |     |    SQS Queue     |
  | Services         |---->|  (audit events)  |---->| (audit-queue)    |
  | (emit audit      |     |                  |     |  + DLQ           |
  |  events)         |     +------------------+     +--------+---------+
  +------------------+                                       |
                                                    +--------v---------+
                                                    |  audit-service   |
                                                    |  (consumer)      |
                                                    +--------+---------+
                                                             |
                                              +--------------+--------------+
                                              |                             |
                                     +--------v---------+         +--------v---------+
                                     |    DynamoDB       |         |    Aurora PG      |
                                     | (hot audit store, |         | (audit_logs table |
                                     |  90-day TTL)      |         |  per tenant,      |
                                     +--------+----------+         |  partitioned)     |
                                              |                    +------------------+
                                     +--------v---------+
                                     | S3 (Glacier Deep  |
                                     |  Archive, 7-year  |
                                     |  retention for    |
                                     |  HIPAA)           |
                                     +------------------+
```

**Audit Event Structure:**

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-11T14:30:00.000Z",
  "event_type": "phi.accessed",
  "actor": {
    "user_id": "usr_abc123",
    "role": "physician",
    "ip_address": "10.0.11.45",
    "user_agent": "Mozilla/5.0..."
  },
  "tenant_id": "tenant_mercy_health",
  "resource": {
    "type": "Patient",
    "id": "pat_xyz789",
    "fhir_id": "Patient/xyz789"
  },
  "action": "read",
  "detail": {
    "fields_accessed": ["name", "birthDate", "condition"],
    "query_parameters": {},
    "response_code": 200
  },
  "context": {
    "encounter_id": "enc_456",
    "break_glass": false,
    "session_id": "sess_def456"
  }
}
```

#### 2.4.5 Network Security Layers

```
  Layer 1: AWS WAF v2
  +--------------------------------------------------+
  | - OWASP Top 10 managed rule group               |
  | - Rate limiting: 2000 req/5min per IP            |
  | - SQL injection detection                        |
  | - XSS pattern matching                           |
  | - Geographic restrictions (configurable)         |
  | - IP reputation lists                            |
  | - Custom rules for healthcare-specific patterns  |
  +--------------------------------------------------+
          |
  Layer 2: CloudFront
  +--------------------------------------------------+
  | - TLS 1.2+ enforcement                          |
  | - Origin access identity for S3                  |
  | - Custom headers for origin verification         |
  | - Field-level encryption (optional, for PII)     |
  +--------------------------------------------------+
          |
  Layer 3: ALB + Security Groups
  +--------------------------------------------------+
  | - Only accepts CloudFront traffic (prefix list)  |
  | - SSL/TLS termination with ACM certificate       |
  | - Security group: ingress 443 only               |
  +--------------------------------------------------+
          |
  Layer 4: ECS Task Security
  +--------------------------------------------------+
  | - No public IP addresses                         |
  | - Task IAM roles (least privilege)               |
  | - Read-only root filesystem                      |
  | - No privileged containers                       |
  | - Secrets injected from Secrets Manager          |
  | - Security group: ingress from ALB-SG only       |
  +--------------------------------------------------+
          |
  Layer 5: Data Layer
  +--------------------------------------------------+
  | - No internet gateway route                      |
  | - Security group: ingress from ECS-SG only       |
  | - Encryption at rest (KMS CMK)                   |
  | - Encryption in transit (TLS)                    |
  | - IAM authentication (Aurora, DynamoDB)          |
  | - Row-level security (PostgreSQL RLS)            |
  +--------------------------------------------------+
```

#### 2.4.6 SMART on FHIR Authorization

OpenMedRecord implements the SMART on FHIR authorization framework to enable
third-party applications (e.g., clinical decision support tools, patient apps)
to securely access FHIR data.

```
  Third-Party App                  OpenMedRecord
  ===============                  =============

  1. App discovers SMART endpoints
     GET /.well-known/smart-configuration

  2. App initiates EHR launch or standalone launch
     GET /auth/authorize?
         response_type=code&
         client_id=app_123&
         redirect_uri=https://app.example.com/callback&
         scope=launch patient/Observation.read&
         state=random_state&
         aud=https://openmedrecord.health/fhir

  3. User authenticates and approves scopes
     (Consent screen with granular scope display)

  4. Authorization code returned
     302 -> https://app.example.com/callback?code=xyz&state=random_state

  5. App exchanges code for tokens
     POST /auth/token
     {
       "grant_type": "authorization_code",
       "code": "xyz",
       "redirect_uri": "https://app.example.com/callback",
       "client_id": "app_123"
     }

  6. Response includes FHIR context
     {
       "access_token": "eyJ...",
       "token_type": "Bearer",
       "scope": "launch patient/Observation.read",
       "patient": "Patient/xyz789",         <-- launch context
       "encounter": "Encounter/enc_456"     <-- launch context
     }

  7. App accesses FHIR resources with scoped token
     GET /fhir/Patient/xyz789/Observation
     Authorization: Bearer eyJ...
```

**Supported SMART Scopes:**

| Scope Pattern              | Example                           | Description            |
|----------------------------|-----------------------------------|------------------------|
| `patient/<Resource>.read`  | `patient/Observation.read`        | Patient-context read   |
| `patient/<Resource>.write` | `patient/MedicationRequest.write` | Patient-context write  |
| `user/<Resource>.read`     | `user/Patient.read`               | User-context read      |
| `user/<Resource>.write`    | `user/Encounter.write`            | User-context write     |
| `system/<Resource>.read`   | `system/Patient.read`             | Backend service access |
| `launch`                   | `launch`                          | EHR launch context     |
| `launch/patient`           | `launch/patient`                  | Standalone patient pick|
| `openid fhirUser`          | `openid fhirUser`                 | Identity claims        |
| `offline_access`           | `offline_access`                  | Refresh token          |

---

### 2.5 Integration Architecture

#### 2.5.1 FHIR R4 API Design

The `fhir-gateway` service exposes a fully compliant FHIR R4 RESTful API.

**Supported Interactions:**

| Interaction    | Endpoint Pattern                           | Description                |
|----------------|--------------------------------------------|----------------------------|
| Read           | `GET /fhir/<Resource>/<id>`                | Read resource by ID        |
| Search         | `GET /fhir/<Resource>?<params>`            | Search with parameters     |
| Create         | `POST /fhir/<Resource>`                    | Create new resource        |
| Update         | `PUT /fhir/<Resource>/<id>`                | Full resource update       |
| Patch          | `PATCH /fhir/<Resource>/<id>`              | Partial update (JSON Patch)|
| Delete         | `DELETE /fhir/<Resource>/<id>`             | Logical delete             |
| History        | `GET /fhir/<Resource>/<id>/_history`       | Version history            |
| Capabilities   | `GET /fhir/metadata`                       | CapabilityStatement        |
| Batch/Trans.   | `POST /fhir/`                              | Bundle processing          |
| Bulk Export    | `GET /fhir/$export`                        | Async NDJSON export        |

**Supported Resources:**

Patient, Encounter, Observation, Condition, MedicationRequest,
MedicationStatement, AllergyIntolerance, Procedure, DiagnosticReport,
ServiceRequest, Immunization, CarePlan, CareTeam, Practitioner,
PractitionerRole, Organization, Location, Schedule, Slot, Appointment,
DocumentReference, AuditEvent, Provenance, OperationOutcome.

#### 2.5.2 HL7v2 Interface Engine

For legacy system integration, OpenMedRecord includes an HL7v2 interface
engine that translates between HL7v2 messages and internal FHIR resources.

```
  External System              OpenMedRecord
  ===============              =============

  +---------------+    MLLP/TCP    +------------------+     +----------------+
  | Legacy HIS    |--------------->| HL7v2 Interface  |---->| FHIR Gateway   |
  | (ADT, ORM,    |    or HTTPS    | Engine           |     | (create/update |
  |  ORU, SIU)    |<---------------| (ECS Fargate)    |<----| FHIR resources)|
  +---------------+                +------------------+     +----------------+
                                          |
                                   +------v------+
                                   | Message     |
                                   | Translation |
                                   | Rules       |
                                   +------+------+
                                          |
                                   +------v------+
                                   | DynamoDB    |
                                   | (message    |
                                   |  log/queue) |
                                   +-------------+
```

**Supported HL7v2 Message Types:**

| Message Type | Direction | Description                          |
|-------------|-----------|--------------------------------------|
| ADT^A01     | Inbound   | Patient admission                    |
| ADT^A02     | Inbound   | Patient transfer                     |
| ADT^A03     | Inbound   | Patient discharge                    |
| ADT^A04     | Inbound   | Patient registration                 |
| ADT^A08     | Both      | Patient information update           |
| ORM^O01     | Outbound  | Order message                        |
| ORU^R01     | Inbound   | Observation result                   |
| SIU^S12     | Both      | Schedule information unsolicited     |
| MDM^T02     | Inbound   | Original document notification       |
| DFT^P03     | Outbound  | Detailed financial transaction       |

#### 2.5.3 Event-Driven Integration Patterns

```
  Pattern 1: Event Notification (Fan-out)
  ========================================

  order-service                          Subscribers
  +-------------+    EventBridge    +---+---+---+---+
  | order.placed|---->[  Bus  ]---->| A | N | F | C |
  +-------------+                   | u | o | H | D |
                                    | d | t | I | S |
                                    | i | i | R |   |
                                    | t | f |   |   |
                                    +---+---+---+---+

  Pattern 2: Command with Reply (Request/Response over events)
  =============================================================

  order-service          SQS          pharmacy-system
  +-------------+   +---------+   +------------------+
  | prescription|-->| rx-queue|-->| process Rx       |
  | .submitted  |   +---------+   | validate, fill   |
  +-------------+                 +--------+---------+
                                           |
  order-service          SQS              |
  +-------------+   +---------+           |
  | update order|<--| rx-reply|<----------+
  | status      |   | -queue  |  prescription.filled
  +-------------+   +---------+

  Pattern 3: Event Sourcing (Audit Trail)
  ========================================

  Any Service           EventBridge         audit-service
  +----------+    +------------------+    +-------------+
  | domain   |--->| openmedrecord    |--->| append-only |
  | event    |    | event bus        |    | event store |
  +----------+    +------------------+    | (DynamoDB + |
                                          |  S3 archive)|
                                          +-------------+
```

#### 2.5.4 External System Connectivity

```
  +-------------------------------------------------------------------+
  |                     OpenMedRecord Platform                        |
  |                                                                   |
  |  +---------------+  +----------------+  +--------------------+    |
  |  | FHIR R4 API   |  | HL7v2 Engine   |  | Webhook/Event API  |    |
  |  +-------+-------+  +--------+-------+  +---------+----------+    |
  +----------|-------------------|----------------------|--------------+
             |                   |                      |
  +----------v---+  +-----------v----+  +---------------v-----------+
  | EHR Systems   |  | Lab Systems    |  | Third-Party Apps          |
  | (Epic, Cerner |  | (LIS via       |  | (CDS Hooks, SMART apps,  |
  |  via FHIR)    |  |  HL7v2 ORU)    |  |  patient portals,        |
  +--------------+  +----------------+  |  mobile apps)             |
                                        +---------------------------+
  +--------------+  +----------------+  +---------------------------+
  | Pharmacy/PBM |  | Imaging (PACS) |  | Public Health Agencies    |
  | (NCPDP/FHIR) |  | (DICOM/FHIR)  |  | (eCR, immunization       |
  +--------------+  +----------------+  |  registries via FHIR)     |
                                        +---------------------------+
  +--------------+  +----------------+
  | Payer/Ins.   |  | HIE / HIN      |
  | (X12/FHIR)   |  | (TEFCA/IHE)    |
  +--------------+  +----------------+
```

---

## 3. API Design

### 3.1 RESTful API Conventions

**Base URL:** `https://api.openmedrecord.health/api/v1`

**Common Headers:**

| Header                | Required | Description                            |
|-----------------------|----------|----------------------------------------|
| `Authorization`       | Yes      | `Bearer <access_token>`                |
| `X-Tenant-ID`        | Yes      | Tenant identifier for multi-tenancy    |
| `X-Request-ID`       | No       | Client-generated correlation ID (UUID) |
| `X-Correlation-ID`   | No       | Cross-service trace correlation        |
| `Content-Type`       | Yes*     | `application/json` (for write ops)     |
| `Accept`             | No       | `application/json` (default)           |
| `If-Match`           | No*      | ETag for optimistic concurrency        |
| `If-None-Match`      | No       | ETag for conditional GET (caching)     |

> **Security Requirement:** The server MUST validate that the `X-Tenant-ID`
> header matches the `tenant_id` claim in the JWT token on every request.
> Mismatches MUST be rejected with HTTP 403 Forbidden and logged as potential
> attack attempts (event type `security.tenant_mismatch`, severity CRITICAL).
> This prevents tenant impersonation via header manipulation.

**Standard Response Envelope:**

```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-02-11T14:30:00.000Z",
    "version": "1.0"
  }
}
```

**Error Response:**

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid patient identifier format",
    "details": [
      {
        "field": "mrn",
        "issue": "MRN must be alphanumeric, 6-20 characters",
        "value": "AB"
      }
    ]
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2026-02-11T14:30:01.000Z"
  }
}
```

**Pagination:**

```json
{
  "status": "success",
  "data": [ ... ],
  "pagination": {
    "total": 1250,
    "limit": 50,
    "offset": 100,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTUwfQ=="
  }
}
```

The API supports both offset-based pagination (for UI table views) and
cursor-based pagination (for large data sets and streaming).

### 3.2 Versioning Strategy

- **URL Path Versioning:** `/api/v1/`, `/api/v2/`
- Major versions indicate breaking changes.
- Minor/non-breaking changes are added within the same version.
- Deprecated versions are supported for a minimum of 12 months.
- FHIR endpoints use the FHIR versioning model: `/fhir/R4/`.

### 3.3 Rate Limiting

| Client Type         | Rate Limit              | Window   | Burst   |
|---------------------|-------------------------|----------|---------|
| Backend service     | 1,000 requests          | 1 minute | 100     |
| Clinician-facing    | 300 requests            | 1 minute | 50      |
| Patient-facing      | 60 requests             | 1 minute | 10      |
| SMART on FHIR app   | 300 requests            | 1 minute | 50      |
| Bulk export         | 10 concurrent exports   | --       | --      |
| Public (unauth.)    | 20 requests             | 1 minute | 5       |

Rate limits are applied consistently across both `/api/v1/` (REST) and `/fhir/`
(FHIR R4) endpoints. The same token bucket algorithm is used for both surfaces.

Rate limit headers are returned on every response:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 997
X-RateLimit-Reset: 1707660000
Retry-After: 30  (only on 429 responses)
```

### 3.4 Key Endpoint Examples

#### Patient Service

```
GET    /api/v1/patients                     # Search patients
GET    /api/v1/patients/{id}                # Get patient by ID
POST   /api/v1/patients                     # Register new patient
PUT    /api/v1/patients/{id}                # Update patient
PATCH  /api/v1/patients/{id}                # Partial update
DELETE /api/v1/patients/{id}                # Soft delete (deactivate)
GET    /api/v1/patients/{id}/encounters     # Patient encounters
GET    /api/v1/patients/{id}/observations   # Patient observations
GET    /api/v1/patients/{id}/conditions     # Patient conditions
GET    /api/v1/patients/{id}/medications    # Patient medications
GET    /api/v1/patients/{id}/timeline       # Unified clinical timeline
POST   /api/v1/patients/match              # Probabilistic patient matching
```

#### Clinical Service

```
GET    /api/v1/encounters                        # Search encounters
POST   /api/v1/encounters                        # Create encounter
PUT    /api/v1/encounters/{id}                   # Update encounter
PATCH  /api/v1/encounters/{id}/status            # Update encounter status

POST   /api/v1/observations                      # Record observation
GET    /api/v1/observations?patient={pid}&code={loinc}  # Search observations

POST   /api/v1/conditions                        # Record condition/diagnosis
PUT    /api/v1/conditions/{id}                   # Update condition
PATCH  /api/v1/conditions/{id}/clinical-status   # Update clinical status

POST   /api/v1/clinical-notes                    # Create clinical note
GET    /api/v1/clinical-notes/{id}               # Retrieve note
PUT    /api/v1/clinical-notes/{id}/sign          # Sign/finalize note

POST   /api/v1/allergies                         # Record allergy
PUT    /api/v1/allergies/{id}                    # Update allergy
```

#### Order Service

```
POST   /api/v1/orders                            # Place new order
GET    /api/v1/orders/{id}                       # Get order details
PUT    /api/v1/orders/{id}                       # Update order
PATCH  /api/v1/orders/{id}/status                # Update order status
DELETE /api/v1/orders/{id}                       # Cancel order
POST   /api/v1/orders/{id}/result                # Submit order result

POST   /api/v1/prescriptions                     # Create prescription
GET    /api/v1/prescriptions/{id}                # Get prescription
POST   /api/v1/prescriptions/{id}/refill         # Request refill
POST   /api/v1/prescriptions/{id}/discontinue    # Discontinue medication
```

#### Scheduling Service

```
GET    /api/v1/schedules                                    # List schedules
POST   /api/v1/schedules                                    # Create schedule
GET    /api/v1/schedules/{id}/slots?date={date}             # Available slots
POST   /api/v1/appointments                                 # Book appointment
GET    /api/v1/appointments/{id}                            # Get appointment
PUT    /api/v1/appointments/{id}                            # Update appointment
PATCH  /api/v1/appointments/{id}/status                     # Check-in / cancel
GET    /api/v1/appointments?practitioner={id}&date={date}   # Provider schedule
```

#### FHIR R4 Endpoints

```
GET    /fhir/metadata                                       # CapabilityStatement
GET    /fhir/Patient/{id}                                   # Read patient
GET    /fhir/Patient?family=Smith&birthdate=1980-01-01      # Search patients
GET    /fhir/Observation?patient={id}&category=vital-signs  # Vitals
GET    /fhir/Condition?patient={id}&clinical-status=active  # Active problems
GET    /fhir/MedicationRequest?patient={id}&status=active   # Active meds
POST   /fhir/$export                                        # Bulk data export
GET    /fhir/$export/{job_id}                               # Export status
GET    /.well-known/smart-configuration                     # SMART discovery
```

---

## 4. Data Model

### 4.1 Core Entity Relationship Diagram

```
                                  +------------------+
                                  |     tenants      |
                                  |------------------|
                                  | id          (PK) |
                                  | name             |
                                  | schema_name      |
                                  | status           |
                                  +--------+---------+
                                           |
                            +--------------+--------------+
                            |                             |
                   +--------v---------+          +--------v---------+
                   |   users          |          |   locations      |
                   |------------------|          |------------------|
                   | id          (PK) |          | id          (PK) |
                   | tenant_id   (FK) |          | tenant_id   (FK) |
                   | cognito_sub      |          | name             |
                   | email            |          | type             |
                   | role_id     (FK) |          | address          |
                   +--------+---------+          +--------+---------+
                            |                             |
                            |         +-------------------+
                            |         |
                   +--------v---------v---+
                   |    patients          |
                   |----------------------|
          +------->| id             (PK)  |<-------+
          |        | tenant_id      (FK)  |        |
          |        | mrn           (UQ)   |        |
          |        | fhir_id       (UQ)   |        |
          |        | given_name           |        |
          |        | family_name          |        |
          |        | birth_date           |        |
          |        | gender               |        |
          |        +----------+-----------+        |
          |                   |                    |
          |        +----------v-----------+        |
          |        |    encounters        |        |
          |        |----------------------|        |
          |  +---->| id             (PK)  |<----+  |
          |  |     | patient_id     (FK)  |     |  |
          |  |     | practitioner_id(FK)  |     |  |
          |  |     | location_id    (FK)  |     |  |
          |  |     | type                 |     |  |
          |  |     | status               |     |  |
          |  |     | period_start         |     |  |
          |  |     | period_end           |     |  |
          |  |     +----------+-----------+     |  |
          |  |                |                 |  |
    +-----+--+-----+---------+--------+--------+--+------+
    |     |  |     |         |        |        |  |      |
+---v--+  |  | +---v----+ +-v------+ +v-----+ | +v----+ |
|allergy|  |  | |observ. | |condit. | |orders| | |meds | |
|intol. |  |  | |--------|.|--------| |------| | |-----| |
|-------|  |  | |id  (PK)| |id (PK) | |id(PK)| | |id(PK| |
|id (PK)|  |  | |pat.(FK)| |pat(FK) | |pat FK| | |patFK| |
|pat(FK)|  |  | |enc.(FK)| |enc(FK) | |encFK | | |encFK| |
|enc(FK)|  |  | |code    | |code    | |type  | | |code | |
|code   |  |  | |value   | |status  | |stat  | | |dose | |
|type   |  |  | |status  | |onset   | |prior | | |route| |
+-------+  |  | +--------+ +--------+ +------+ | +-----+ |
           |  |                                 |         |
           |  |     +---------------------------+         |
           |  |     |                                     |
           |  |  +--v-----------+          +--------------v--+
           |  |  |clinical_notes|          |  audit_logs     |
           |  |  |--------------|          |-----------------|
           |  |  | id      (PK) |          | id         (PK) |
           |  |  | enc_id  (FK) |          | timestamp       |
           |  |  | author  (FK) |          | actor_id   (FK) |
           |  |  | type         |          | action          |
           |  |  | content      |          | resource_type   |
           |  |  | status       |          | resource_id     |
           |  |  | signed_at    |          | detail    (JSONB)|
           |  |  +--------------+          +-----------------+
           |  |
           |  +-- FK relationships shown with (FK) annotation
           +---- All tables include: created_at, updated_at, created_by
```

### 4.2 Key Table Schemas

#### `patients`

```sql
CREATE TABLE patients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mrn             VARCHAR(20) NOT NULL,
    fhir_id         VARCHAR(64) NOT NULL,
    given_name      VARCHAR(100) NOT NULL,
    family_name     VARCHAR(100) NOT NULL,
    birth_date      DATE NOT NULL,
    gender          VARCHAR(20) NOT NULL CHECK (gender IN (
                        'male', 'female', 'other', 'unknown')),
                    -- Note: 'gender' is administrative sex per FHIR Patient.gender.
                    -- See gender_identity and sex_assigned_at_birth for clinical use.
    sex_assigned_at_birth VARCHAR(20) CHECK (sex_assigned_at_birth IN (
                        'male', 'female', 'unknown')),
    gender_identity VARCHAR(50),     -- Separate from administrative sex per USCDI v3
    sexual_orientation VARCHAR(50),  -- USCDI v3
    preferred_name  VARCHAR(200),
    preferred_language VARCHAR(35),  -- BCP-47 code (e.g., 'en-US', 'es-419')
    deceased        BOOLEAN DEFAULT FALSE,
    deceased_date   TIMESTAMPTZ,
    address         JSONB DEFAULT '[]'::jsonb,
    telecom         JSONB DEFAULT '[]'::jsonb,
    identifiers     JSONB DEFAULT '[]'::jsonb,
    marital_status  VARCHAR(20),
    language        VARCHAR(10) DEFAULT 'en',
    race            JSONB,
    ethnicity       JSONB,
    ssn_encrypted   BYTEA,           -- Fernet/AES encrypted
    ssn_hmac        VARCHAR(64),     -- HMAC index for exact-match search
    preferred_pharmacy_id UUID,
    emergency_contact JSONB,
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID NOT NULL REFERENCES users(id),
    version         INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT uq_patients_mrn UNIQUE (mrn),
    CONSTRAINT uq_patients_fhir_id UNIQUE (fhir_id)
);

-- Indexes
CREATE INDEX idx_patients_family_name ON patients (lower(family_name));
CREATE INDEX idx_patients_birth_date ON patients (birth_date);
CREATE INDEX idx_patients_given_family ON patients (lower(family_name), lower(given_name));
CREATE INDEX idx_patients_identifiers ON patients USING GIN (identifiers);
CREATE INDEX idx_patients_active ON patients (active) WHERE active = true;
CREATE INDEX idx_patients_created_at ON patients (created_at);
```

#### `encounters`

```sql
CREATE TABLE encounters (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id        UUID NOT NULL REFERENCES patients(id),
    practitioner_id   UUID NOT NULL REFERENCES users(id),
    location_id       UUID REFERENCES locations(id),
    type              VARCHAR(50) NOT NULL CHECK (type IN (
                          'ambulatory', 'emergency', 'inpatient',
                          'observation', 'virtual')),
    status            VARCHAR(30) NOT NULL CHECK (status IN (
                          'planned', 'arrived', 'triaged', 'in-progress',
                          'onleave', 'finished', 'cancelled',
                          'entered-in-error')),
    class             VARCHAR(30) NOT NULL,
    priority          VARCHAR(20),
    reason_code       JSONB DEFAULT '[]'::jsonb,
    diagnosis         JSONB DEFAULT '[]'::jsonb,
    period_start      TIMESTAMPTZ NOT NULL,
    period_end        TIMESTAMPTZ,
    length_minutes    INTEGER,
    disposition       VARCHAR(100),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by        UUID NOT NULL REFERENCES users(id),
    version           INTEGER NOT NULL DEFAULT 1,

    CONSTRAINT chk_enc_period CHECK (period_end IS NULL OR period_end >= period_start)
);

-- Indexes
CREATE INDEX idx_encounters_patient_id ON encounters (patient_id);
CREATE INDEX idx_encounters_practitioner ON encounters (practitioner_id);
CREATE INDEX idx_encounters_status ON encounters (status);
CREATE INDEX idx_encounters_period ON encounters (period_start DESC);
CREATE INDEX idx_encounters_patient_period ON encounters (patient_id, period_start DESC);
CREATE INDEX idx_encounters_type_status ON encounters (type, status);
```

#### `observations`

```sql
CREATE TABLE observations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES patients(id),
    encounter_id    UUID REFERENCES encounters(id),
    practitioner_id UUID REFERENCES users(id),
    category        VARCHAR(50) NOT NULL CHECK (category IN (
                        'vital-signs', 'laboratory', 'imaging',
                        'social-history', 'exam', 'survey')),
    code            VARCHAR(20) NOT NULL,
    code_system     VARCHAR(100) NOT NULL DEFAULT 'http://loinc.org',
    display         VARCHAR(255),
    status          VARCHAR(20) NOT NULL CHECK (status IN (
                        'registered', 'preliminary', 'final',
                        'amended', 'corrected', 'cancelled',
                        'entered-in-error')),
    value_type      VARCHAR(20) CHECK (value_type IN (
                        'Quantity', 'CodeableConcept', 'string',
                        'boolean', 'integer', 'Range', 'Ratio',
                        'Period', 'dateTime')),
    value_string    VARCHAR(1000),
    value_numeric   DECIMAL(18, 6),
    value_unit      VARCHAR(50),
    value_code      VARCHAR(100),
    reference_range JSONB,
    interpretation  VARCHAR(20),
    effective_dt    TIMESTAMPTZ NOT NULL,
    issued_dt       TIMESTAMPTZ NOT NULL DEFAULT now(),
    note            TEXT,
    component       JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      UUID NOT NULL REFERENCES users(id),
    version         INTEGER NOT NULL DEFAULT 1
);

-- Indexes
CREATE INDEX idx_obs_patient_id ON observations (patient_id);
CREATE INDEX idx_obs_encounter_id ON observations (encounter_id);
CREATE INDEX idx_obs_code ON observations (code);
CREATE INDEX idx_obs_category ON observations (category);
CREATE INDEX idx_obs_patient_code ON observations (patient_id, code, effective_dt DESC);
CREATE INDEX idx_obs_patient_category ON observations (patient_id, category, effective_dt DESC);
CREATE INDEX idx_obs_effective_dt ON observations (effective_dt DESC);
CREATE INDEX idx_obs_status ON observations (status);
```

#### `audit_logs` (Aurora -- long-term queryable store)

```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type      VARCHAR(50) NOT NULL,
    actor_id        UUID,
    actor_role      VARCHAR(50),
    actor_ip        INET,
    actor_ua        TEXT,
    action          VARCHAR(20) NOT NULL CHECK (action IN (
                        'create', 'read', 'update', 'delete',
                        'search', 'login', 'logout', 'export',
                        'break_glass', 'consent_change')),
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     UUID,
    tenant_id       VARCHAR(100) NOT NULL,
    detail          JSONB,
    outcome         VARCHAR(20) NOT NULL CHECK (outcome IN (
                        'success', 'failure', 'error')),
    session_id      VARCHAR(100)
) PARTITION BY RANGE (timestamp);

-- Monthly partitions (managed by pg_partman or application)
CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE audit_logs_2026_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- ... ongoing monthly partitions created automatically

-- Indexes
CREATE INDEX idx_audit_timestamp ON audit_logs (timestamp DESC);
CREATE INDEX idx_audit_actor ON audit_logs (actor_id, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_logs (resource_type, resource_id);
CREATE INDEX idx_audit_event_type ON audit_logs (event_type, timestamp DESC);
CREATE INDEX idx_audit_tenant ON audit_logs (tenant_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_logs (action, timestamp DESC);
```

#### `roles` and RBAC Tables

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(tenant_id, name)
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type VARCHAR(100) NOT NULL,
    operation VARCHAR(50) NOT NULL CHECK (operation IN ('create', 'read', 'update', 'delete', 'search', 'export')),
    description TEXT,
    UNIQUE(resource_type, operation)
);

CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    assigned_at TIMESTAMPTZ DEFAULT now(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);
```

#### `allergy_intolerances`

```sql
CREATE TABLE allergy_intolerances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(id),
    clinical_status VARCHAR(20) NOT NULL CHECK (clinical_status IN ('active', 'inactive', 'resolved')),
    verification_status VARCHAR(20) CHECK (verification_status IN ('unconfirmed', 'presumed', 'confirmed', 'refuted', 'entered-in-error')),
    type VARCHAR(20) CHECK (type IN ('allergy', 'intolerance')),
    category VARCHAR(20)[] CHECK (category <@ ARRAY['food', 'medication', 'environment', 'biologic']::VARCHAR[]),
    criticality VARCHAR(20) CHECK (criticality IN ('low', 'high', 'unable-to-assess')),
    code_system VARCHAR(100),
    code VARCHAR(50),
    code_display VARCHAR(500),
    onset_datetime TIMESTAMPTZ,
    recorded_date TIMESTAMPTZ DEFAULT now(),
    recorder_id UUID REFERENCES users(id),
    note TEXT,
    reaction JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    version INTEGER DEFAULT 1
);
CREATE INDEX idx_allergy_patient_status ON allergy_intolerances(patient_id, clinical_status);
```

#### `clinical_notes`

```sql
CREATE TABLE clinical_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(id),
    note_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('in-progress', 'preliminary', 'final', 'amended', 'entered-in-error')),
    author_id UUID NOT NULL REFERENCES users(id),
    content_encrypted BYTEA,
    content_hash VARCHAR(64),
    is_psychotherapy_note BOOLEAN DEFAULT FALSE,
    is_42cfr_part2 BOOLEAN DEFAULT FALSE,
    signed_at TIMESTAMPTZ,
    signed_by UUID REFERENCES users(id),
    signature BYTEA,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    version INTEGER DEFAULT 1
);
CREATE INDEX idx_notes_patient ON clinical_notes(patient_id, encounter_id);
CREATE INDEX idx_notes_type ON clinical_notes(note_type, status);
```

#### `appointments`

```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id),
    provider_id UUID NOT NULL REFERENCES users(id),
    location_id UUID,
    status VARCHAR(20) NOT NULL CHECK (status IN ('proposed', 'pending', 'booked', 'arrived', 'fulfilled', 'cancelled', 'noshow', 'entered-in-error', 'checked-in', 'waitlist')),
    appointment_type VARCHAR(100),
    reason_code VARCHAR(100),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,
    comment TEXT,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    version INTEGER DEFAULT 1
);
CREATE INDEX idx_appt_provider_time ON appointments(provider_id, start_time);
CREATE INDEX idx_appt_patient ON appointments(patient_id, start_time);
CREATE INDEX idx_appt_status ON appointments(status, start_time);
```

#### `immunizations`

```sql
CREATE TABLE immunizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('completed', 'entered-in-error', 'not-done')),
    vaccine_code VARCHAR(20) NOT NULL,
    vaccine_code_system VARCHAR(100) DEFAULT 'http://hl7.org/fhir/sid/cvx',
    vaccine_display VARCHAR(500),
    occurrence_datetime TIMESTAMPTZ NOT NULL,
    lot_number VARCHAR(50),
    site_code VARCHAR(20),
    route_code VARCHAR(20),
    dose_quantity DECIMAL,
    performer_id UUID REFERENCES users(id),
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    version INTEGER DEFAULT 1
);
CREATE INDEX idx_immunization_patient ON immunizations(patient_id, occurrence_datetime);
```

#### Additional Indexes for Existing Tables

The following indexes are applied to tables defined in the ER diagram (Section
2.3.2) that do not have separate DDL sections above. All of these tables also
include `updated_at TIMESTAMPTZ DEFAULT now()` and `version INTEGER DEFAULT 1`
columns for optimistic concurrency control.

```sql
-- conditions table
CREATE INDEX idx_conditions_patient_status ON conditions(patient_id, clinical_status);

-- medications table
CREATE INDEX idx_medications_patient_status ON medications(patient_id, status);

-- orders table
CREATE INDEX idx_orders_patient_type ON orders(patient_id, order_type, status);
CREATE INDEX idx_orders_requester ON orders(requester_id);
```

### 4.3 Indexing Strategy

| Strategy               | Use Case                                    | Implementation            |
|------------------------|---------------------------------------------|---------------------------|
| B-tree (default)       | Equality and range queries on scalar columns| Primary keys, timestamps  |
| GIN (Generalized Inv.) | JSONB containment and key-exists queries    | `identifiers`, `address`  |
| Partial indexes         | Frequently filtered subsets                 | `WHERE active = true`     |
| Composite indexes       | Multi-column lookups                        | `(patient_id, code, dt)`  |
| Covering indexes        | Index-only scans for common queries         | `INCLUDE (display, value)`|
| Expression indexes      | Case-insensitive name search                | `lower(family_name)`      |

### 4.4 Partitioning Strategy

| Table          | Partition Method | Partition Key  | Retention     | Notes                |
|----------------|-----------------|----------------|---------------|----------------------|
| `audit_logs`   | Range           | `timestamp`    | 7 years       | Monthly partitions   |
| `observations` | Range           | `effective_dt` | Indefinite    | Quarterly partitions |
| `encounters`   | Range           | `period_start` | Indefinite    | Yearly partitions    |
| `orders`       | Range           | `ordered_dt`   | Indefinite    | Quarterly partitions |

Partition management is automated using `pg_partman` extension:

```sql
SELECT partman.create_parent(
    p_parent_table := 'public.audit_logs',
    p_control := 'timestamp',
    p_type := 'range',
    p_interval := '1 month',
    p_premake := 3
);
```

---

## 5. Security Controls

### 5.1 HIPAA Technical Safeguard Mapping

| HIPAA Requirement (164.312)            | Implementation                                         |
|----------------------------------------|--------------------------------------------------------|
| **Access Control (a)(1)**              | RBAC + ABAC via auth-service; JWT-based authorization  |
| **Unique User Identification (a)(2)(i)** | Cognito user pools; unique `cognito_sub` per user    |
| **Emergency Access Procedure (a)(2)(ii)** | Break-glass mechanism with audit trail             |
| **Automatic Logoff (a)(2)(iii)**       | 15-min access token; 8-hour session with idle timeout  |
| **Encryption/Decryption (a)(2)(iv)**   | AES-256 at rest (KMS CMK); TLS 1.2+ in transit        |
| **Audit Controls (b)**                 | Comprehensive audit pipeline; 7-year retention; S3/Glacier |
| **Integrity Controls (c)(1)**          | Optimistic concurrency (version column); checksums     |
| **Auth for Transmission (d)**          | TLS 1.2+ on all channels; mTLS for inter-service      |
| **Transmission Security (e)(1)**       | KMS-encrypted channels; VPC isolation; no public data  |
| **Person/Entity Auth (d)**             | OAuth2/OIDC + MFA; SMART on FHIR for third-party apps |

### 5.2 Encryption Specifications

```
  Key Hierarchy
  =============

  +---------------------------+
  |   AWS KMS                 |
  |                           |
  |  +---------------------+  |
  |  | CMK: omr-master-key |  |     Root of trust (AWS-managed HSM)
  |  | (AES-256, auto-     |  |     Auto-rotates annually
  |  |  rotate, multi-AZ)  |  |
  |  +----------+----------+  |
  +-------------|-------------+
                |
       +--------+--------+
       |                  |
  +----v------+    +------v------+
  | Data Key  |    | Data Key    |
  | (Aurora   |    | (DynamoDB   |
  |  TDE)     |    |  table)     |
  +-----------+    +-------------+

  Application-Level Encryption (for high-sensitivity fields):
  ===========================================================

  +-------------------+     +-------------------+
  | Plaintext PHI     |     | Encrypted PHI     |
  | (SSN, genomic     |---->| (AES-256-GCM,     |
  |  data)            |     |  envelope enc.    |
  +-------------------+     |  with KMS data    |
                            |  key)             |
                            +-------------------+
```

**Application-Level Encryption** is applied to fields classified as
high-sensitivity beyond the standard database-level TDE:

| Field               | Table        | Encryption               | Searchable     |
|---------------------|-------------|--------------------------|----------------|
| SSN                 | patients     | AES-256-GCM (envelope)   | HMAC index     |
| Genomic data        | observations | AES-256-GCM (envelope)   | No             |
| Substance use notes | clinical_notes | AES-256-GCM (envelope) | No             |
| Psych notes (42 CFR)| clinical_notes | AES-256-GCM (envelope) | No             |
| Credit card (if any)| billing      | Tokenization (external)  | Token lookup   |

### 5.3 Access Control Matrix

| Resource          | system_admin | org_admin | physician | nurse | pharmacist | lab_tech | scheduler | billing | patient |
|-------------------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Patient demogr.   | CRUD | CRUD | CRUD | CRU | R | R | R | R | R* |
| Encounters        | CRUD | CRUD | CRUD | CRU | R | R | R | R | R* |
| Observations      | CRUD | R | CRUD | CRU | R | CR | -- | -- | R* |
| Conditions        | CRUD | R | CRUD | CR | R | -- | -- | R | R* |
| Medications       | CRUD | R | CRUD | R | CRU | -- | -- | R | R* |
| Orders (lab)      | CRUD | R | CRUD | CR | R | CRU | -- | R | R* |
| Orders (Rx)       | CRUD | R | CRUD | R | CRU | -- | -- | R | R* |
| Clinical notes    | CRUD | R | CRUD | CR | R | -- | -- | -- | R* |
| Appointments      | CRUD | CRUD | CRU | CRU | -- | -- | CRUD | R | CRU*|
| Users             | CRUD | CRUD | R | R | R | R | R | R | -- |
| Audit logs        | R | R | -- | -- | -- | -- | -- | -- | -- |
| System config     | CRUD | R | -- | -- | -- | -- | -- | -- | -- |

Legend: C=Create, R=Read, U=Update, D=Delete, *=Own records only, --=No access

### 5.4 Audit Event Catalog

| Event Type                   | Severity | PHI? | Trigger                          |
|------------------------------|----------|------|----------------------------------|
| `auth.login.success`        | INFO     | No   | Successful authentication        |
| `auth.login.failure`        | WARN     | No   | Failed authentication attempt    |
| `auth.mfa.challenge`        | INFO     | No   | MFA challenge issued             |
| `auth.logout`               | INFO     | No   | User logged out                  |
| `auth.token.refresh`        | INFO     | No   | Token refreshed                  |
| `phi.patient.read`          | INFO     | Yes  | Patient record accessed          |
| `phi.patient.create`        | INFO     | Yes  | New patient registered           |
| `phi.patient.update`        | INFO     | Yes  | Patient record modified          |
| `phi.patient.search`        | INFO     | Yes  | Patient search executed          |
| `phi.encounter.read`        | INFO     | Yes  | Encounter accessed               |
| `phi.encounter.create`      | INFO     | Yes  | New encounter started            |
| `phi.observation.create`    | INFO     | Yes  | Observation recorded             |
| `phi.observation.read`      | INFO     | Yes  | Observation accessed             |
| `phi.medication.prescribe`  | INFO     | Yes  | Medication prescribed            |
| `phi.note.read`             | INFO     | Yes  | Clinical note accessed           |
| `phi.note.sign`             | INFO     | Yes  | Clinical note signed             |
| `phi.export.bulk`           | WARN     | Yes  | Bulk data export initiated       |
| `phi.break_glass`           | CRITICAL | Yes  | Emergency access invoked         |
| `admin.user.create`         | INFO     | No   | New user account created         |
| `admin.user.deactivate`     | WARN     | No   | User account deactivated         |
| `admin.role.change`         | WARN     | No   | User role modified               |
| `admin.config.change`       | WARN     | No   | System configuration changed     |
| `system.error`              | ERROR    | Maybe| Unhandled system error           |
| `integration.fhir.request`  | INFO     | Yes  | External FHIR API request        |
| `integration.hl7.message`   | INFO     | Yes  | HL7v2 message processed          |

---

## 6. Infrastructure

### 6.1 CDK Module Structure

```
infrastructure/
  cdk/
    bin/
      app.ts                          # CDK app entry point
    lib/
      stacks/
        network-stack.ts              # VPC, subnets, NAT, VPC endpoints
        security-stack.ts             # WAF, KMS keys, security groups
        database-stack.ts             # Aurora, DynamoDB, ElastiCache
        compute-stack.ts              # ECS cluster, Fargate services
        auth-stack.ts                 # Cognito user pool, identity pool
        frontend-stack.ts             # S3 bucket, CloudFront distribution
        messaging-stack.ts            # EventBridge bus, SQS queues
        monitoring-stack.ts           # CloudWatch dashboards, alarms, X-Ray
        pipeline-stack.ts             # CI/CD pipeline (CodePipeline)
        dns-stack.ts                  # Route 53 hosted zone, records
      constructs/
        fargate-service.ts            # Reusable ECS Fargate service construct
        aurora-cluster.ts             # Reusable Aurora cluster construct
        sqs-with-dlq.ts              # SQS queue with dead-letter queue
        encrypted-bucket.ts           # S3 bucket with KMS encryption
        waf-rules.ts                  # WAF rule groups
      config/
        environments.ts               # Environment-specific configuration
        constants.ts                  # Shared constants
    cdk.json
    tsconfig.json
    package.json
```

**Stack Dependency Graph:**

```
  network-stack
       |
       +---> security-stack
       |          |
       +---> database-stack ----+
       |          |             |
       +---> auth-stack         |
       |          |             |
       +---> compute-stack <----+
       |          |
       +---> messaging-stack
       |          |
       +---> frontend-stack
       |          |
       +---> monitoring-stack
       |          |
       +---> dns-stack
       |
       +---> pipeline-stack
```

### 6.2 CI/CD Pipeline Design

```
  +----------+     +-----------+     +------------+     +-------------+
  |  GitHub   |     |  GitHub   |     |  Build &   |     |   Deploy    |
  |  Push /   |---->|  Actions  |---->|  Test      |---->|   Stage     |
  |  PR       |     |  Trigger  |     |            |     |             |
  +----------+     +-----------+     +------------+     +-------------+
                                           |                    |
                                    +------v------+      +------v------+
                                    | Lint & SAST |      | CDK Deploy  |
                                    | (ruff, bandit|      | to staging  |
                                    |  semgrep)   |      +------+------+
                                    +------+------+             |
                                           |             +------v------+
                                    +------v------+      | Integration |
                                    | Unit Tests  |      | Tests       |
                                    | (pytest,    |      | (staging)   |
                                    |  coverage)  |      +------+------+
                                    +------+------+             |
                                           |             +------v------+
                                    +------v------+      | Manual      |
                                    | Build Docker|      | Approval    |
                                    | Images      |      | Gate        |
                                    | Push to ECR |      +------+------+
                                    +-------------+             |
                                                         +------v------+
                                                         | CDK Deploy  |
                                                         | to prod     |
                                                         | (blue/green)|
                                                         +-------------+
```

**Pipeline Stages:**

| Stage              | Tools                          | Gate Criteria                    |
|--------------------|--------------------------------|----------------------------------|
| **Source**         | GitHub (webhooks)              | Branch: `main`, `release/*`      |
| **Lint**           | ruff, eslint, prettier         | Zero errors                      |
| **SAST**           | bandit, semgrep, Trivy         | No high/critical findings        |
| **Unit Test**      | pytest (backend), vitest (FE)  | >90% coverage, all pass          |
| **Build**          | Docker multi-stage builds      | Image builds successfully        |
| **Image Scan**     | Trivy, ECR enhanced scanning   | No critical CVEs                 |
| **Deploy Staging** | CDK deploy                     | Stack deploys without error      |
| **Integration**    | pytest (integration suite)     | All integration tests pass       |
| **E2E Test**       | Playwright                     | All E2E scenarios pass           |
| **DAST**           | OWASP ZAP                      | No high findings                 |
| **Approval**       | Manual gate                    | Authorized approver signs off    |
| **Deploy Prod**    | CDK deploy (blue/green)        | Health checks pass               |

### 6.3 Environment Strategy

| Environment   | Purpose                            | Data           | Scale       | Access            |
|---------------|------------------------------------|----------------|-------------|-------------------|
| **dev**       | Feature development, debugging     | Synthetic      | Minimal     | Developers        |
| **staging**   | Pre-production validation, QA      | Anonymized prod| Prod-like   | QA + Dev leads    |
| **prod**      | Production workloads               | Real PHI       | Full        | Ops + on-call     |
| **dr**        | Disaster recovery (passive)        | Replicated     | Standby     | Ops (failover)    |

**Environment Isolation:**

- Separate AWS accounts per environment (AWS Organizations).
- Separate Cognito user pools per environment.
- Network isolation: no cross-environment VPC peering.
- Secrets Manager secrets scoped per environment.
- CDK context files parametrize stack configuration per environment.

### 6.4 Monitoring and Alerting

**Observability Stack:**

```
  +-------------------+    +-------------------+    +-------------------+
  | Application Logs  |    |    Metrics        |    | Distributed Traces|
  | (structured JSON) |    | (OpenTelemetry)   |    | (AWS X-Ray)       |
  +--------+----------+    +--------+----------+    +--------+----------+
           |                        |                        |
  +--------v----------+    +--------v----------+    +--------v----------+
  | CloudWatch Logs   |    | CloudWatch Metrics|    | X-Ray Service Map |
  | (log groups per   |    | (custom + AWS     |    | (end-to-end       |
  |  service)         |    |  built-in)        |    |  request tracing) |
  +--------+----------+    +--------+----------+    +-------------------+
           |                        |
  +--------v-----------+   +--------v----------+
  | CloudWatch Logs    |   | CloudWatch Alarms |
  | Insights (queries) |   | (threshold +      |
  +--------------------+   |  anomaly detect.) |
                           +--------+----------+
                                    |
                           +--------v----------+
                           |   SNS Topics      |
                           | - PagerDuty       |
                           | - Slack (#alerts) |
                           | - Email (on-call) |
                           +-------------------+
```

**Key Metrics and Alarms:**

| Metric                              | Threshold            | Alarm Severity | Action           |
|--------------------------------------|----------------------|----------------|------------------|
| API latency p99                     | > 2 seconds          | Warning        | Slack alert      |
| API latency p99                     | > 5 seconds          | Critical       | PagerDuty        |
| API error rate (5xx)                | > 1%                 | Warning        | Slack alert      |
| API error rate (5xx)                | > 5%                 | Critical       | PagerDuty        |
| ECS task count (service)            | < desired count      | Critical       | PagerDuty        |
| Aurora CPU utilization              | > 80%                | Warning        | Slack alert      |
| Aurora CPU utilization              | > 95%                | Critical       | PagerDuty        |
| Aurora free storage                 | < 20 GB              | Warning        | Slack alert      |
| Aurora replication lag              | > 100 ms             | Warning        | Slack alert      |
| Redis memory usage                  | > 80%                | Warning        | Slack alert      |
| Redis evictions                     | > 0 (sustained)      | Warning        | Slack alert      |
| SQS DLQ message count              | > 0                  | Warning        | Slack alert      |
| SQS DLQ message count              | > 100                | Critical       | PagerDuty        |
| SQS queue age (oldest message)     | > 5 minutes          | Warning        | Slack alert      |
| Auth failure rate                   | > 10/min             | Warning        | Security alert   |
| Auth failure rate                   | > 50/min             | Critical       | Security + PD    |
| Break-glass event                   | Any occurrence       | Critical       | Privacy officer  |
| WAF blocked requests                | > 1000/hour          | Warning        | Security alert   |
| Certificate expiry                  | < 30 days            | Warning        | Slack alert      |
| Health check failure                | Any target unhealthy | Critical       | PagerDuty        |

---

## 7. Disaster Recovery

### 7.1 RTO/RPO Targets

| Tier               | Components                                   | RTO        | RPO        |
|--------------------|----------------------------------------------|------------|------------|
| **Tier 1** (Critical)| Patient lookup, clinical documentation, auth | 15 minutes | 5 minutes  |
| **Tier 2** (High)    | Order entry, medication management           | 30 minutes | 15 minutes |
| **Tier 3** (Medium)  | Scheduling, notifications                    | 2 hours    | 1 hour     |
| **Tier 4** (Low)     | Reporting, analytics, bulk export            | 4 hours    | 1 hour     |

### 7.2 Multi-AZ Strategy (Primary Region)

```
  Primary Region: us-east-1
  =========================

  AZ-a                    AZ-b                    AZ-c
  +-------------------+   +-------------------+   +-------------------+
  | ECS Tasks (all    |   | ECS Tasks (all    |   | ECS Tasks (all    |
  |  services, equal  |   |  services, equal  |   |  services, equal  |
  |  task count)      |   |  task count)      |   |  task count)      |
  +-------------------+   +-------------------+   +-------------------+
  | Aurora Writer     |   | Aurora Reader     |   | Aurora Reader     |
  | (primary)         |   | (auto-failover)   |   | (auto-failover)   |
  +-------------------+   +-------------------+   +-------------------+
  | Redis Primary     |   | Redis Replica     |   | Redis Replica     |
  +-------------------+   +-------------------+   +-------------------+
  | NAT Gateway       |   | NAT Gateway       |   | NAT Gateway       |
  +-------------------+   +-------------------+   +-------------------+

  Automatic Failover:
  - Aurora: automatic failover to reader in 30-60 seconds
  - ECS: tasks redistribute across healthy AZs
  - Redis: automatic failover to replica
  - ALB: health checks remove unhealthy targets in ~30 seconds
```

### 7.3 Cross-Region Failover

```
  Primary Region (us-east-1)              DR Region (us-west-2)
  ==========================              ======================

  +------------------------+              +------------------------+
  | Active Workloads       |              | Passive / Warm Standby |
  |                        |              |                        |
  | ECS Services (active)  |              | ECS Services (scaled   |
  | Aurora Writer + 2 Read |   Repl.      |  to minimum)           |
  | DynamoDB (active)      |----------->  | Aurora Global DB       |
  | ElastiCache (active)   |   Global     |  (read replica)        |
  | S3 (primary)           |   Tables     | DynamoDB Global Tables |
  +------------------------+              | ElastiCache (cold)     |
                                          | S3 (CRR)              |
         Route 53                         +------------------------+
  +------------------+
  | Health Check     |     Failover:
  | (primary region) |     1. Route 53 health check fails
  | Failover routing |     2. DNS switches to DR region
  | policy           |     3. Aurora Global DB promotes DR reader
  +------------------+     4. ECS services scale up in DR
                           5. DynamoDB Global Tables already active
                           6. Verify via runbook checklist
```

**Cross-Region Replication:**

| Component          | Replication Method                | Lag Target  |
|--------------------|-----------------------------------|-------------|
| Aurora PostgreSQL  | Aurora Global Database            | < 1 second  |
| DynamoDB           | Global Tables (multi-region)      | < 1 second  |
| S3                 | Cross-Region Replication (CRR)    | < 15 minutes|
| Secrets Manager    | Cross-region secret replication   | Near-instant|
| ElastiCache        | Global Datastore                  | < 1 second  |
| ECR Images         | Cross-region replication          | < 5 minutes |

### 7.4 Backup Procedures

| Resource             | Backup Method                   | Frequency      | Retention       |
|----------------------|---------------------------------|----------------|-----------------|
| Aurora PostgreSQL    | Automated snapshots             | Continuous      | 35 days         |
| Aurora PostgreSQL    | Manual snapshots                | Weekly          | 1 year          |
| Aurora PostgreSQL    | Point-in-time recovery          | 5-min granularity| 35 days        |
| DynamoDB             | Point-in-time recovery          | Continuous      | 35 days         |
| DynamoDB             | On-demand backups               | Daily           | 1 year          |
| S3 (PHI buckets)    | Versioning + lifecycle          | Every write     | 7 years         |
| S3 (audit archives)  | Glacier Deep Archive           | On archive      | 7 years         |
| ECS Task Definitions | Version history in ECR/CDK     | Every deploy    | All versions    |
| Secrets Manager      | Automatic versioning           | Every rotation  | All versions    |
| CDK/IaC State        | Git repository                 | Every commit    | Indefinite      |

**Recovery Procedures:**

| Scenario                     | Procedure                                  | RTO Estimate |
|------------------------------|--------------------------------------------|--------------|
| Single AZ failure            | Automatic (ECS + Aurora failover)          | < 2 minutes  |
| Aurora writer failure        | Automatic failover to reader               | < 60 seconds |
| Accidental data deletion     | Point-in-time recovery to new cluster      | 15-30 minutes|
| Full region outage           | Manual DR failover via runbook             | 15-60 minutes|
| Ransomware / data corruption | Restore from clean snapshot, forensics     | 1-4 hours    |
| Secret compromise            | Rotate via Secrets Manager, redeploy       | 15-30 minutes|

### 7.5 Cache Degradation Strategy

When ElastiCache is unavailable or cold (e.g., after regional failover), all
services MUST gracefully degrade by falling back to direct Aurora reads. Response
latency may increase by 50--200ms during cache warming. Services MUST NOT fail
or return errors if the cache is unavailable. Cache warming is automatic as
requests flow through the system; no manual intervention is required.

### 7.6 DR Testing Schedule

| Test Type             | Frequency  | Success Criteria                                      | Owner          |
|-----------------------|------------|-------------------------------------------------------|----------------|
| Within-region failover| Monthly    | All Tier 1 services operational within 15 min RTO     | On-call SRE    |
| Cross-region failover | Quarterly  | All tiers meet RTO targets, data integrity verified   | SRE Lead       |
| Backup restoration    | Monthly    | Restore completes within 30 min, data integrity check | DBA            |
| Audit trail continuity| Quarterly  | Zero gaps in audit trail across failover boundary     | Compliance     |

DR test results are documented with timestamps, success/failure status, and
remediation items. Failed tests generate P1 issues in the backlog.

### 7.7 JWT Signing Key Replication

JWT signing keys are replicated to the DR region via Secrets Manager cross-region
secret replication. Both regions use identical signing key material to ensure
tokens issued in the primary region validate in the DR region during failover.
This prevents forced re-authentication during a clinical emergency. Key
replication lag is monitored; replication failure triggers a P1 alert.

---

## 8. Technology Decisions (ADRs)

### ADR-001: FastAPI over Django / Flask

**Status:** Accepted

**Context:** We need a Python web framework for building microservices that
handle healthcare data. The framework must support high-performance async I/O,
strong input validation, automatic OpenAPI documentation, and modern Python
type hints.

**Decision:** Use FastAPI as the primary backend framework.

**Rationale:**

| Criterion               | FastAPI              | Django REST         | Flask               |
|--------------------------|----------------------|---------------------|---------------------|
| Async support            | Native (ASGI)       | Limited (ASGI new)  | Requires extensions |
| Performance              | High (Starlette)    | Moderate             | Moderate            |
| Input validation         | Built-in (Pydantic) | Serializers          | Manual / Marshmallow|
| OpenAPI generation       | Automatic            | via drf-spectacular | Manual / Flasgger  |
| Type safety              | Pydantic v2 native  | Limited              | Limited             |
| Learning curve           | Low-moderate         | High (monolithic)   | Low                 |
| Microservice fit         | Excellent            | Poor (monolithic)   | Good                |
| Dependency injection     | Built-in             | None                 | None                |
| WebSocket support        | Built-in             | Channels (separate) | Flask-SocketIO      |

**Consequences:**
- Pydantic v2 provides compile-time-like validation for FHIR resources.
- Native async enables efficient handling of concurrent database and external
  service calls.
- Automatic OpenAPI spec generation reduces documentation drift.
- Smaller ecosystem than Django for admin/ORM; mitigated by using SQLAlchemy
  and building custom admin UI in React.

---

### ADR-002: Aurora PostgreSQL over Plain RDS PostgreSQL

**Status:** Accepted

**Context:** We need a relational database that can handle healthcare workloads
with strict durability, high availability, and strong consistency requirements.
The database must support HIPAA-compliant encryption and multi-AZ deployment.

**Decision:** Use Amazon Aurora PostgreSQL as the primary relational database.

**Rationale:**

| Criterion                  | Aurora PostgreSQL       | RDS PostgreSQL          |
|----------------------------|-------------------------|-------------------------|
| Storage durability         | 6 copies across 3 AZs  | 2 copies (Multi-AZ)    |
| Failover time              | < 30 seconds            | 60-120 seconds          |
| Read replicas              | Up to 15 (same storage) | Up to 15 (async repl.) |
| Storage auto-scaling       | Up to 128 TB            | Manual (max 64 TB)     |
| Backup/restore             | Continuous, incremental | Daily snapshots         |
| Global database            | Yes (cross-region)      | Read replicas only     |
| Performance                | 3-5x standard PG        | Baseline PostgreSQL    |
| Cost                       | ~20% more than RDS      | Baseline               |

**Consequences:**
- 6-copy storage provides durability beyond what plain RDS offers, critical
  for PHI.
- Sub-30-second failover meets Tier 1 RTO requirements.
- Global Database enables cross-region DR with < 1 second replication lag.
- Higher cost is justified by operational simplicity and healthcare compliance
  requirements.
- Aurora-specific features (e.g., parallel query, fast cloning for dev/test)
  provide additional operational benefits.

---

### ADR-003: ECS Fargate over EKS (Kubernetes)

**Status:** Accepted

**Context:** We need a container orchestration platform for running
microservices. The platform must minimize operational overhead while providing
the scalability, networking, and security features required for healthcare
workloads.

**Decision:** Use Amazon ECS with Fargate launch type.

**Rationale:**

| Criterion               | ECS Fargate              | EKS (Fargate or EC2)     |
|--------------------------|--------------------------|--------------------------|
| Operational complexity   | Low (fully managed)      | High (control plane mgmt)|
| Learning curve           | Low                      | High (Kubernetes)        |
| Cluster management       | None (serverless)        | Control plane + nodes    |
| IAM integration          | Native task roles         | IRSA (more complex)      |
| Service discovery        | Cloud Map (built-in)     | CoreDNS + services       |
| Load balancing           | Native ALB integration   | ALB Ingress Controller   |
| Cost (small-medium)      | Lower TCO                | Higher (control plane $) |
| Ecosystem/portability    | AWS-locked               | Kubernetes portable      |
| Secrets integration      | Native Secrets Manager   | External Secrets Operator|
| Auto-scaling             | Application Auto Scaling | HPA + Karpenter          |

**Consequences:**
- Significantly reduced operational burden: no node management, no Kubernetes
  version upgrades, no cluster autoscaler tuning.
- Native AWS IAM integration simplifies the security model for HIPAA
  compliance.
- Trade-off: reduced portability compared to Kubernetes. Mitigated by keeping
  application code container-runtime-agnostic (standard Dockerfiles, no
  ECS-specific APIs in application code).
- If the organization later requires multi-cloud or on-premises deployment, a
  migration path to EKS or standard Kubernetes exists because services are
  standard Docker containers behind a load balancer.

---

### ADR-004: React over Angular / Vue

**Status:** Accepted

**Context:** We need a frontend framework for building a complex clinical user
interface. The UI must support real-time data updates, complex forms (clinical
documentation), accessibility (WCAG 2.1 AA), and a large component ecosystem
for healthcare-specific widgets.

**Decision:** Use React 18 with TypeScript.

**Rationale:**

| Criterion               | React                  | Angular                | Vue                    |
|--------------------------|------------------------|------------------------|------------------------|
| Ecosystem size           | Largest                | Large                  | Moderate               |
| TypeScript support       | Excellent              | Native                 | Good (Vue 3)           |
| Healthcare UI libraries  | Most available         | Some                   | Few                    |
| Learning curve           | Moderate               | Steep                  | Low-moderate           |
| Performance (large apps) | Excellent (concurrent) | Good                   | Good                   |
| Community / hiring       | Largest pool           | Large                  | Growing                |
| State management         | Flexible (many options)| Built-in (RxJS)       | Pinia/Vuex             |
| Server components        | Yes (React 18+)       | No                     | No                     |
| Accessibility tooling    | Strong (react-aria)    | Strong (CDK a11y)     | Moderate               |
| Open-source EHR examples | Most (OpenMRS, etc.)   | Few                    | Few                    |

**Consequences:**
- Largest talent pool simplifies hiring and community contributions to the
  open-source project.
- Flexible architecture allows choosing the best state management (Zustand for
  global state, TanStack Query for server state) rather than being locked to
  a framework opinion.
- Trade-off: React's flexibility means more architectural decisions upfront.
  Mitigated by establishing clear project conventions and a shared component
  library.
- TypeScript provides compile-time safety for complex FHIR resource types.

---

### ADR-005: EventBridge over Direct Service-to-Service Calls

**Status:** Accepted

**Context:** Microservices need to communicate for cross-cutting concerns such
as audit logging, notifications, cache invalidation, and data synchronization.
We need a communication pattern that is resilient, loosely coupled, and supports
the addition of new consumers without modifying producers.

**Decision:** Use Amazon EventBridge as the primary inter-service communication
mechanism for asynchronous workflows, with SQS queues for consumer-side
buffering and dead-letter handling.

**Rationale:**

| Criterion                | EventBridge + SQS      | Direct HTTP Calls       | SNS + SQS             |
|--------------------------|------------------------|--------------------------|------------------------|
| Coupling                 | Loose (schema-based)   | Tight (URL + contract)  | Loose (topic-based)   |
| Resilience               | Built-in retry + DLQ   | Circuit breaker needed  | Retry + DLQ           |
| Fan-out                  | Native (rule targets)  | Manual (call each svc)  | Native (subscriptions)|
| Content-based routing    | Yes (event patterns)   | No                      | Filter policies (limited)|
| Schema registry          | Yes (built-in)         | OpenAPI (separate)      | No                    |
| Event replay             | Archive + replay       | Not possible             | Not possible          |
| New consumer addition    | Add rule (no producer change)| Modify producer   | Add subscription      |
| Latency                  | ~100-500ms             | ~10-50ms                | ~100-500ms            |
| Cost at scale            | Moderate               | Low (no per-event cost) | Low-moderate          |

**Consequences:**
- Producers publish events without knowing consumers. Adding a new consumer
  (e.g., a new analytics service) requires zero changes to existing services.
- EventBridge Schema Registry provides a contract for event shapes, enabling
  independent service evolution.
- Archive and replay capability is critical for healthcare: if a bug caused
  incorrect audit processing, events can be replayed after the fix.
- Trade-off: higher latency than direct calls (~100-500ms vs ~10-50ms). This
  is acceptable because asynchronous workflows (audit, notifications, sync)
  are not latency-sensitive. Synchronous user-facing reads still use direct
  HTTP calls through the ALB.
- SQS queues between EventBridge and consumers provide buffering, rate
  control, and dead-letter queues for failed processing.

---

### ADR-006: Schema-per-Tenant Multi-tenancy

**Status:** Accepted

**Context:** Multi-tenant SaaS serving healthcare organizations requires strong
data isolation for PHI. Options considered: row-level isolation (tenant_id column
on every table), schema-per-tenant (PostgreSQL search_path), and
database-per-tenant (separate Aurora clusters).

**Decision:** Use schema-per-tenant with PostgreSQL `search_path`, with a shared
schema for cross-tenant platform tables (`tenants`, `global_config`,
`tenant_users`).

**Rationale:**

| Criterion              | Row-Level Isolation    | Schema-per-Tenant      | Database-per-Tenant    |
|------------------------|------------------------|------------------------|------------------------|
| Data isolation strength| Weak (application-enforced) | Strong (schema boundary) | Strongest (DB boundary)|
| Query performance      | Requires tenant_id in every query | Clean queries within schema | Clean queries |
| Migration complexity   | Single migration       | Per-schema migration   | Per-database migration |
| Tenant onboarding      | Instant (add row)      | Fast (create schema ~1s)| Slow (provision cluster)|
| Tenant count limit     | Unlimited              | ~1,000 practical       | ~100 practical (cost)  |
| Cross-tenant analytics | Easy                   | Possible via shared schema | Complex              |
| Cost per tenant        | Lowest                 | Low                    | Highest                |
| Regulatory compliance  | Requires RLS diligence | Schema-level isolation | Strongest separation   |

**Consequences:**
- Schema isolation prevents accidental cross-tenant data access even if
  application code has bugs -- queries physically cannot reach another schema.
- Database migrations must run per-schema, managed by a migration orchestrator.
- Connection pooling is schema-aware (SET search_path per connection).
- Schema names are validated via `_validate_schema_name()` regex to prevent
  SQL injection in search_path statements.
- RLS policies serve as defense-in-depth, not primary isolation mechanism.
- If a tenant requires database-level isolation (e.g., government/military),
  a dedicated Aurora cluster can be provisioned as an exception.

---

### ADR-007: DynamoDB for Sessions and Audit Hot Store

**Status:** Accepted

**Context:** Sessions require low-latency reads and automatic TTL-based
expiration. Audit events require high-write-throughput ingestion with time-based
queries and automatic archival.

**Decision:** Use DynamoDB for session storage and the audit event hot store
(90-day window). Aurora remains the long-term durable audit store.

**Rationale:**

| Criterion              | DynamoDB               | Aurora (sessions)      | Redis (sessions)       |
|------------------------|------------------------|------------------------|------------------------|
| TTL expiration         | Built-in, automatic    | Requires cron/trigger  | Built-in               |
| Durability             | Multi-AZ, persistent   | Multi-AZ, persistent   | In-memory, volatile    |
| Write throughput       | On-demand, auto-scale  | Connection-limited     | Very high (in-memory)  |
| Cross-region (DR)      | Global Tables           | Global Database        | Global Datastore       |
| Session persistence    | Survives restarts      | Survives restarts      | Lost on restart        |
| Cost (write-heavy)     | Low (on-demand)        | Medium (Aurora IOPS)   | Medium (memory cost)   |

**Consequences:**
- Sessions survive Redis restarts (which was the primary concern with
  Redis-only sessions for a healthcare system).
- DynamoDB Global Tables provide cross-region session consistency for DR
  failover without re-authentication.
- Audit events MUST be confirmed written to Aurora before DynamoDB TTL eviction
  to prevent data loss. A reconciliation job compares DynamoDB event IDs against
  Aurora weekly.
- Two query interfaces for audit data: DynamoDB for recent events (< 90 days),
  Aurora for historical queries.

---

### ADR-008: Dual API Surface (REST + FHIR)

**Status:** Accepted

**Context:** The system needs both a clinician-facing API optimized for UI
workflows and a standards-compliant FHIR R4 API for interoperability, ONC
certification, and the 21st Century Cures Act.

**Decision:** Maintain two API surfaces: `/api/v1/` (REST with custom schemas)
and `/fhir/` (FHIR R4 with standard resources). Both read and write to the same
underlying relational data store through a shared service layer.

**Rationale:**
- FHIR's resource model doesn't map efficiently to clinical UI needs (e.g.,
  a patient chart view requires assembling 6+ FHIR resources).
- The REST API can optimize for clinician workflows (fewer round-trips, custom
  projections, bulk operations).
- The FHIR API meets regulatory requirements (ONC, CMS Patient Access, Cures).
- Maintaining both is less costly than forcing FHIR semantics on the UI or
  building a FHIR-to-custom translation layer in the frontend.

**Rules:**
- Both surfaces share the same service layer and database transactions.
- The FHIR gateway is a thin translation layer, not a separate data store.
- SMART on FHIR scopes apply to `/fhir/` endpoints; `/api/v1/` uses RBAC.
- Data written via `/api/v1/` is immediately readable via `/fhir/` and vice
  versa.
- Rate limits are unified across both surfaces (per-user, not per-surface).

**Consequences:**
- Dual surface increases API surface area to maintain and test.
- Schema changes must be reflected in both REST schemas and FHIR mappings.
- Security testing must cover both surfaces independently.

---

## Appendix A: Glossary

| Term     | Definition                                                           |
|----------|----------------------------------------------------------------------|
| ABAC     | Attribute-Based Access Control                                       |
| ACM      | AWS Certificate Manager                                              |
| ADR      | Architecture Decision Record                                         |
| ALB      | Application Load Balancer                                            |
| AZ       | Availability Zone                                                    |
| CDS      | Clinical Decision Support                                            |
| CDK      | AWS Cloud Development Kit                                            |
| CMK      | Customer-Managed Key (KMS)                                           |
| CRR      | Cross-Region Replication (S3)                                        |
| DLQ      | Dead-Letter Queue                                                    |
| eCR      | Electronic Case Reporting                                            |
| EHR      | Electronic Health Record                                             |
| FHIR     | Fast Healthcare Interoperability Resources                           |
| HL7      | Health Level Seven International                                     |
| HIPAA    | Health Insurance Portability and Accountability Act                  |
| HIE      | Health Information Exchange                                          |
| MLLP     | Minimum Lower Layer Protocol (HL7v2 transport)                       |
| MRN      | Medical Record Number                                                |
| mTLS     | Mutual TLS (bidirectional certificate authentication)                |
| OIDC     | OpenID Connect                                                       |
| PHI      | Protected Health Information                                         |
| RBAC     | Role-Based Access Control                                            |
| RLS      | Row-Level Security (PostgreSQL)                                      |
| RPO      | Recovery Point Objective                                             |
| RTO      | Recovery Time Objective                                              |
| SMART    | Substitutable Medical Applications, Reusable Technologies            |
| TEFCA    | Trusted Exchange Framework and Common Agreement                      |
| TDE      | Transparent Data Encryption                                          |

## Appendix B: Reference Standards

| Standard              | Version  | Usage                                      |
|-----------------------|----------|--------------------------------------------|
| HL7 FHIR             | R4 (4.0.1)| Primary interoperability standard         |
| HL7 v2               | 2.5.1    | Legacy system integration                  |
| SMART on FHIR        | 2.0      | Third-party app authorization              |
| OAuth 2.0            | RFC 6749 | Authorization framework                    |
| OpenID Connect        | 1.0      | Identity layer                             |
| LOINC                 | 2.77     | Observation/lab code system                |
| SNOMED CT             | 2024-09  | Clinical terminology                       |
| ICD-10-CM             | 2026     | Diagnosis codes                            |
| CPT                   | 2026     | Procedure codes                            |
| RxNorm                | Current  | Medication terminology                     |
| WCAG                  | 2.1 AA   | Web accessibility                          |
| HIPAA                 | 2013 Omnibus| Privacy and security rule                |
| NIST SP 800-53       | Rev. 5   | Security and privacy controls              |

---

*This document is maintained in version control. Changes require review and
approval by the architecture team. For questions or proposed changes, open an
issue or pull request in the OpenMedRecord repository.*
