#!/usr/bin/env python3
"""
OpenMedRecord CDK Application Entry Point.

Defines the deployment topology for the OpenMedRecord EHR system across
AWS environments.  Each stack encapsulates a single infrastructure concern
and exports values consumed by dependent stacks.
"""

import os

import aws_cdk as cdk

from stacks.compute_stack import ComputeStack
from stacks.database_stack import DatabaseStack
from stacks.frontend_stack import FrontendStack
from stacks.monitoring_stack import MonitoringStack
from stacks.security_stack import SecurityStack
from stacks.vpc_stack import VpcStack

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

ACCOUNT = os.environ.get("CDK_DEFAULT_ACCOUNT", os.environ.get("AWS_ACCOUNT_ID"))
REGION = os.environ.get("CDK_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))

if not ACCOUNT:
    raise RuntimeError(
        "AWS account ID is required. Set CDK_DEFAULT_ACCOUNT or AWS_ACCOUNT_ID."
    )

env = cdk.Environment(account=ACCOUNT, region=REGION)

STAGE = os.environ.get("STAGE", "staging")  # staging | production
PROJECT = "OpenMedRecord"
DOMAIN_NAME = os.environ.get("DOMAIN_NAME", "openmedrecord.health")

# ---------------------------------------------------------------------------
# Tags applied to every resource in every stack
# ---------------------------------------------------------------------------

GLOBAL_TAGS = {
    "Project": PROJECT,
    "Stage": STAGE,
    "ManagedBy": "CDK",
    "CostCenter": "engineering",
    "DataClassification": "PHI",
    "Compliance": "HIPAA",
}

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = cdk.App()

# Apply global tags
for key, value in GLOBAL_TAGS.items():
    cdk.Tags.of(app).add(key, value)

# -- Networking --------------------------------------------------------------
vpc_stack = VpcStack(
    app,
    f"{PROJECT}-Vpc-{STAGE}",
    env=env,
    stage=STAGE,
)

# -- Security ----------------------------------------------------------------
security_stack = SecurityStack(
    app,
    f"{PROJECT}-Security-{STAGE}",
    env=env,
    stage=STAGE,
    vpc=vpc_stack.vpc,
)
security_stack.add_dependency(vpc_stack)

# -- Data Tier ---------------------------------------------------------------
database_stack = DatabaseStack(
    app,
    f"{PROJECT}-Database-{STAGE}",
    env=env,
    stage=STAGE,
    vpc=vpc_stack.vpc,
    kms_key=security_stack.data_key,
    db_security_group=security_stack.db_security_group,
    cache_security_group=security_stack.cache_security_group,
)
database_stack.add_dependency(security_stack)

# -- Compute -----------------------------------------------------------------
compute_stack = ComputeStack(
    app,
    f"{PROJECT}-Compute-{STAGE}",
    env=env,
    stage=STAGE,
    vpc=vpc_stack.vpc,
    cluster_security_group=security_stack.ecs_security_group,
    db_secret=database_stack.db_secret,
    redis_endpoint=database_stack.redis_endpoint,
    kms_key=security_stack.data_key,
    domain_name=DOMAIN_NAME,
)
compute_stack.add_dependency(database_stack)

# -- Frontend ----------------------------------------------------------------
frontend_stack = FrontendStack(
    app,
    f"{PROJECT}-Frontend-{STAGE}",
    env=env,
    stage=STAGE,
    domain_name=DOMAIN_NAME,
    api_alb=compute_stack.alb,
)
frontend_stack.add_dependency(compute_stack)

# -- Monitoring & Observability ----------------------------------------------
monitoring_stack = MonitoringStack(
    app,
    f"{PROJECT}-Monitoring-{STAGE}",
    env=env,
    stage=STAGE,
    ecs_cluster=compute_stack.cluster,
    alb=compute_stack.alb,
    aurora_cluster=database_stack.aurora_cluster,
    redis_cluster=database_stack.redis_cluster,
    alert_email=os.environ.get("ALERT_EMAIL", "ops@openmedrecord.health"),
)
monitoring_stack.add_dependency(compute_stack)

app.synth()
