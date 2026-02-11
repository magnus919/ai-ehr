"""
Database Stack -- Data tier for OpenMedRecord.

Provisions:
  - Aurora PostgreSQL 16 (Multi-AZ, encrypted, automated backups)
  - DynamoDB tables for audit logs and sessions
  - ElastiCache Redis 7 cluster for caching and rate limiting
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
    aws_ec2 as ec2,
    aws_elasticache as elasticache,
    aws_kms as kms,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class DatabaseStack(Stack):
    """Provisions all persistent data stores for OpenMedRecord."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        stage: str,
        vpc: ec2.IVpc,
        kms_key: kms.IKey,
        db_security_group: ec2.ISecurityGroup,
        cache_security_group: ec2.ISecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._stage = stage
        self._vpc = vpc
        self._kms_key = kms_key

        is_prod = stage == "production"

        # == Aurora PostgreSQL ==================================================
        self.db_secret = secretsmanager.Secret(
            self,
            "AuroraSecret",
            secret_name=f"openmedrecord/{stage}/aurora",
            description="Aurora PostgreSQL credentials for OpenMedRecord",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "openmed_admin"}',
                generate_string_key="password",
                exclude_characters="\"@/\\",
                password_length=32,
            ),
            encryption_key=kms_key,
        )

        # Subnet group for data-tier subnets
        subnet_group = rds.SubnetGroup(
            self,
            "AuroraSubnetGroup",
            description="OpenMedRecord Aurora subnet group",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
        )

        # Parameter group
        parameter_group = rds.ParameterGroup(
            self,
            "AuroraParams",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_16_4,
            ),
            parameters={
                "shared_preload_libraries": "pg_stat_statements,pgaudit",
                "pgaudit.log": "all",
                "pgaudit.log_catalog": "off",
                "log_connections": "1",
                "log_disconnections": "1",
                "log_statement": "ddl",
                "ssl": "1",
                "ssl_min_protocol_version": "TLSv1.2",
            },
        )

        self.aurora_cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            cluster_identifier=f"openmedrecord-{stage}",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_16_4,
            ),
            credentials=rds.Credentials.from_secret(self.db_secret),
            default_database_name="openmedrecord",
            parameter_group=parameter_group,
            subnet_group=subnet_group,
            security_groups=[db_security_group],
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            writer=rds.ClusterInstance.provisioned(
                "Writer",
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.R6G,
                    ec2.InstanceSize.XLARGE if is_prod else ec2.InstanceSize.LARGE,
                ),
                publicly_accessible=False,
                enable_performance_insights=True,
                performance_insight_encryption_key=kms_key,
                performance_insight_retention=rds.PerformanceInsightRetention.MONTHS_1
                if is_prod
                else rds.PerformanceInsightRetention.DEFAULT,
            ),
            readers=[
                rds.ClusterInstance.provisioned(
                    "Reader1",
                    instance_type=ec2.InstanceType.of(
                        ec2.InstanceClass.R6G,
                        ec2.InstanceSize.XLARGE
                        if is_prod
                        else ec2.InstanceSize.LARGE,
                    ),
                    publicly_accessible=False,
                    enable_performance_insights=True,
                    performance_insight_encryption_key=kms_key,
                ),
            ]
            + (
                [
                    rds.ClusterInstance.provisioned(
                        "Reader2",
                        instance_type=ec2.InstanceType.of(
                            ec2.InstanceClass.R6G,
                            ec2.InstanceSize.XLARGE,
                        ),
                        publicly_accessible=False,
                        enable_performance_insights=True,
                        performance_insight_encryption_key=kms_key,
                    ),
                ]
                if is_prod
                else []
            ),
            storage_encrypted=True,
            storage_encryption_key=kms_key,
            backup=rds.BackupProps(
                retention=Duration.days(35 if is_prod else 7),
                preferred_window="03:00-04:00",
            ),
            preferred_maintenance_window="sun:04:00-sun:05:00",
            deletion_protection=is_prod,
            removal_policy=RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY,
            cloudwatch_logs_exports=["postgresql"],
            iam_authentication=True,
            copy_tags_to_snapshot=True,
            monitoring_interval=Duration.seconds(60),
        )

        # == DynamoDB -- Audit Logs =============================================
        self.audit_table = dynamodb.Table(
            self,
            "AuditLogTable",
            table_name=f"openmedrecord-{stage}-audit-logs",
            partition_key=dynamodb.Attribute(
                name="pk",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="sk",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )

        # GSI for querying by user
        self.audit_table.add_global_secondary_index(
            index_name="gsi-user-timestamp",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # GSI for querying by resource
        self.audit_table.add_global_secondary_index(
            index_name="gsi-resource-timestamp",
            partition_key=dynamodb.Attribute(
                name="resource_type",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # == DynamoDB -- Sessions ===============================================
        self.sessions_table = dynamodb.Table(
            self,
            "SessionsTable",
            table_name=f"openmedrecord-{stage}-sessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=kms_key,
            time_to_live_attribute="expires_at",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # == ElastiCache Redis ==================================================
        cache_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description="OpenMedRecord Redis subnet group",
            subnet_ids=[s.subnet_id for s in vpc.isolated_subnets],
            cache_subnet_group_name=f"openmedrecord-{stage}-redis",
        )

        self.redis_cluster = elasticache.CfnReplicationGroup(
            self,
            "RedisCluster",
            replication_group_description=f"OpenMedRecord Redis - {stage}",
            replication_group_id=f"openmedrecord-{stage}",
            engine="redis",
            engine_version="7.1",
            cache_node_type="cache.r6g.large" if is_prod else "cache.t4g.medium",
            num_node_groups=1,
            replicas_per_node_group=2 if is_prod else 1,
            automatic_failover_enabled=True,
            multi_az_enabled=is_prod,
            cache_subnet_group_name=cache_subnet_group.cache_subnet_group_name,
            security_group_ids=[cache_security_group.security_group_id],
            at_rest_encryption_enabled=True,
            kms_key_id=kms_key.key_id,
            transit_encryption_enabled=True,
            transit_encryption_mode="required",
            auto_minor_version_upgrade=True,
            snapshot_retention_limit=7 if is_prod else 1,
            snapshot_window="02:00-03:00",
            preferred_maintenance_window="sun:05:00-sun:06:00",
            port=6379,
        )
        self.redis_cluster.add_dependency(cache_subnet_group)

        # Expose the primary endpoint
        self.redis_endpoint = (
            self.redis_cluster.attr_primary_end_point_address
        )

        # == Outputs ============================================================
        CfnOutput(
            self,
            "AuroraClusterEndpoint",
            value=self.aurora_cluster.cluster_endpoint.hostname,
        )
        CfnOutput(
            self,
            "AuroraReaderEndpoint",
            value=self.aurora_cluster.cluster_read_endpoint.hostname,
        )
        CfnOutput(
            self, "AuroraSecretArn", value=self.db_secret.secret_arn
        )
        CfnOutput(self, "AuditTableName", value=self.audit_table.table_name)
        CfnOutput(
            self, "SessionsTableName", value=self.sessions_table.table_name
        )
        CfnOutput(self, "RedisEndpoint", value=self.redis_endpoint)
