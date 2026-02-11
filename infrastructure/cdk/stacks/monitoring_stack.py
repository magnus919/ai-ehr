"""
Monitoring Stack -- CloudWatch dashboards, alarms, SNS alerting, and CloudTrail.

Provides operational visibility into the OpenMedRecord platform with
actionable alarms for SRE teams.
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_cloudtrail as cloudtrail,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_logs as logs,
    aws_rds as rds,
    aws_s3 as s3,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
)
from constructs import Construct


class MonitoringStack(Stack):
    """Provisions monitoring, alerting, and audit infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        stage: str,
        ecs_cluster: ecs.ICluster,
        alb: elbv2.IApplicationLoadBalancer,
        aurora_cluster: rds.IDatabaseCluster,
        redis_cluster,  # CfnReplicationGroup
        alert_email: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._stage = stage
        is_prod = stage == "production"

        # == SNS Topics =========================================================
        self.critical_topic = sns.Topic(
            self,
            "CriticalAlerts",
            topic_name=f"omr-{stage}-critical-alerts",
            display_name=f"OpenMedRecord {stage} Critical Alerts",
        )
        self.warning_topic = sns.Topic(
            self,
            "WarningAlerts",
            topic_name=f"omr-{stage}-warning-alerts",
            display_name=f"OpenMedRecord {stage} Warning Alerts",
        )

        if alert_email:
            self.critical_topic.add_subscription(
                sns_subs.EmailSubscription(alert_email)
            )
            self.warning_topic.add_subscription(
                sns_subs.EmailSubscription(alert_email)
            )

        critical_action = cw_actions.SnsAction(self.critical_topic)
        warning_action = cw_actions.SnsAction(self.warning_topic)

        # == ALB Alarms =========================================================

        # 5xx error rate > 5% for 5 minutes
        alb_5xx = cw.Alarm(
            self,
            "ALB5xxAlarm",
            alarm_name=f"omr-{stage}-alb-5xx-high",
            alarm_description="ALB 5xx error rate exceeds 5%",
            metric=cw.Metric(
                namespace="AWS/ApplicationELB",
                metric_name="HTTPCode_Target_5XX_Count",
                dimensions_map={
                    "LoadBalancer": alb.load_balancer_full_name,
                },
                statistic="Sum",
                period=Duration.minutes(5),
            ),
            threshold=50,
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        alb_5xx.add_alarm_action(critical_action)

        # Latency p99 > 2 seconds
        alb_latency = cw.Alarm(
            self,
            "ALBLatencyAlarm",
            alarm_name=f"omr-{stage}-alb-latency-high",
            alarm_description="ALB p99 latency exceeds 2 seconds",
            metric=cw.Metric(
                namespace="AWS/ApplicationELB",
                metric_name="TargetResponseTime",
                dimensions_map={
                    "LoadBalancer": alb.load_balancer_full_name,
                },
                statistic="p99",
                period=Duration.minutes(5),
            ),
            threshold=2.0,
            evaluation_periods=3,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        alb_latency.add_alarm_action(warning_action)

        # Unhealthy host count > 0
        unhealthy_hosts = cw.Alarm(
            self,
            "UnhealthyHostsAlarm",
            alarm_name=f"omr-{stage}-unhealthy-hosts",
            alarm_description="One or more ALB targets are unhealthy",
            metric=cw.Metric(
                namespace="AWS/ApplicationELB",
                metric_name="UnHealthyHostCount",
                dimensions_map={
                    "LoadBalancer": alb.load_balancer_full_name,
                },
                statistic="Maximum",
                period=Duration.minutes(1),
            ),
            threshold=0,
            evaluation_periods=3,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
        unhealthy_hosts.add_alarm_action(critical_action)

        # == ECS Alarms =========================================================

        # CPU utilization > 85%
        ecs_cpu = cw.Alarm(
            self,
            "ECSCpuAlarm",
            alarm_name=f"omr-{stage}-ecs-cpu-high",
            alarm_description="ECS cluster CPU utilization exceeds 85%",
            metric=cw.Metric(
                namespace="AWS/ECS",
                metric_name="CPUUtilization",
                dimensions_map={
                    "ClusterName": ecs_cluster.cluster_name,
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=85,
            evaluation_periods=3,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.BREACHING,
        )
        ecs_cpu.add_alarm_action(warning_action)

        # Memory utilization > 85%
        ecs_memory = cw.Alarm(
            self,
            "ECSMemoryAlarm",
            alarm_name=f"omr-{stage}-ecs-memory-high",
            alarm_description="ECS cluster memory utilization exceeds 85%",
            metric=cw.Metric(
                namespace="AWS/ECS",
                metric_name="MemoryUtilization",
                dimensions_map={
                    "ClusterName": ecs_cluster.cluster_name,
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=85,
            evaluation_periods=3,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.BREACHING,
        )
        ecs_memory.add_alarm_action(warning_action)

        # == Aurora Alarms ======================================================

        # CPU utilization > 80%
        aurora_cpu = cw.Alarm(
            self,
            "AuroraCpuAlarm",
            alarm_name=f"omr-{stage}-aurora-cpu-high",
            alarm_description="Aurora CPU utilization exceeds 80%",
            metric=cw.Metric(
                namespace="AWS/RDS",
                metric_name="CPUUtilization",
                dimensions_map={
                    "DBClusterIdentifier": aurora_cluster.cluster_identifier,
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=80,
            evaluation_periods=3,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        aurora_cpu.add_alarm_action(critical_action)

        # Freeable memory < 1 GB
        aurora_memory = cw.Alarm(
            self,
            "AuroraMemoryAlarm",
            alarm_name=f"omr-{stage}-aurora-memory-low",
            alarm_description="Aurora freeable memory below 1 GB",
            metric=cw.Metric(
                namespace="AWS/RDS",
                metric_name="FreeableMemory",
                dimensions_map={
                    "DBClusterIdentifier": aurora_cluster.cluster_identifier,
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=1_073_741_824,  # 1 GB in bytes
            evaluation_periods=3,
            comparison_operator=cw.ComparisonOperator.LESS_THAN_THRESHOLD,
        )
        aurora_memory.add_alarm_action(critical_action)

        # Database connections > 80% of max
        aurora_connections = cw.Alarm(
            self,
            "AuroraConnectionsAlarm",
            alarm_name=f"omr-{stage}-aurora-connections-high",
            alarm_description="Aurora database connections exceed 80% of maximum",
            metric=cw.Metric(
                namespace="AWS/RDS",
                metric_name="DatabaseConnections",
                dimensions_map={
                    "DBClusterIdentifier": aurora_cluster.cluster_identifier,
                },
                statistic="Average",
                period=Duration.minutes(5),
            ),
            threshold=800,  # ~80% of r6g.xlarge max connections
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
        )
        aurora_connections.add_alarm_action(warning_action)

        # == CloudWatch Dashboard ===============================================
        dashboard = cw.Dashboard(
            self,
            "Dashboard",
            dashboard_name=f"OpenMedRecord-{stage}",
        )

        dashboard.add_widgets(
            cw.TextWidget(
                markdown=f"# OpenMedRecord - {stage.upper()} Environment",
                width=24,
                height=1,
            ),
        )

        # ALB row
        dashboard.add_widgets(
            cw.GraphWidget(
                title="ALB Request Count",
                left=[
                    cw.Metric(
                        namespace="AWS/ApplicationELB",
                        metric_name="RequestCount",
                        dimensions_map={
                            "LoadBalancer": alb.load_balancer_full_name,
                        },
                        statistic="Sum",
                        period=Duration.minutes(1),
                    ),
                ],
                width=8,
            ),
            cw.GraphWidget(
                title="ALB Response Time (p50/p95/p99)",
                left=[
                    cw.Metric(
                        namespace="AWS/ApplicationELB",
                        metric_name="TargetResponseTime",
                        dimensions_map={
                            "LoadBalancer": alb.load_balancer_full_name,
                        },
                        statistic=stat,
                        period=Duration.minutes(1),
                        label=stat,
                    )
                    for stat in ["p50", "p95", "p99"]
                ],
                width=8,
            ),
            cw.GraphWidget(
                title="ALB HTTP Errors",
                left=[
                    cw.Metric(
                        namespace="AWS/ApplicationELB",
                        metric_name=f"HTTPCode_Target_{code}_Count",
                        dimensions_map={
                            "LoadBalancer": alb.load_balancer_full_name,
                        },
                        statistic="Sum",
                        period=Duration.minutes(1),
                        label=f"{code}",
                    )
                    for code in ["4XX", "5XX"]
                ],
                width=8,
            ),
        )

        # ECS row
        dashboard.add_widgets(
            cw.GraphWidget(
                title="ECS CPU Utilization",
                left=[
                    cw.Metric(
                        namespace="AWS/ECS",
                        metric_name="CPUUtilization",
                        dimensions_map={
                            "ClusterName": ecs_cluster.cluster_name,
                        },
                        statistic="Average",
                        period=Duration.minutes(1),
                    ),
                ],
                width=8,
            ),
            cw.GraphWidget(
                title="ECS Memory Utilization",
                left=[
                    cw.Metric(
                        namespace="AWS/ECS",
                        metric_name="MemoryUtilization",
                        dimensions_map={
                            "ClusterName": ecs_cluster.cluster_name,
                        },
                        statistic="Average",
                        period=Duration.minutes(1),
                    ),
                ],
                width=8,
            ),
            cw.SingleValueWidget(
                title="Running Tasks",
                metrics=[
                    cw.Metric(
                        namespace="ECS/ContainerInsights",
                        metric_name="RunningTaskCount",
                        dimensions_map={
                            "ClusterName": ecs_cluster.cluster_name,
                        },
                        statistic="Average",
                        period=Duration.minutes(1),
                    ),
                ],
                width=8,
            ),
        )

        # Aurora row
        dashboard.add_widgets(
            cw.GraphWidget(
                title="Aurora CPU Utilization",
                left=[
                    cw.Metric(
                        namespace="AWS/RDS",
                        metric_name="CPUUtilization",
                        dimensions_map={
                            "DBClusterIdentifier": aurora_cluster.cluster_identifier,
                        },
                        statistic="Average",
                        period=Duration.minutes(1),
                    ),
                ],
                width=8,
            ),
            cw.GraphWidget(
                title="Aurora Connections",
                left=[
                    cw.Metric(
                        namespace="AWS/RDS",
                        metric_name="DatabaseConnections",
                        dimensions_map={
                            "DBClusterIdentifier": aurora_cluster.cluster_identifier,
                        },
                        statistic="Average",
                        period=Duration.minutes(1),
                    ),
                ],
                width=8,
            ),
            cw.GraphWidget(
                title="Aurora Latency",
                left=[
                    cw.Metric(
                        namespace="AWS/RDS",
                        metric_name=metric_name,
                        dimensions_map={
                            "DBClusterIdentifier": aurora_cluster.cluster_identifier,
                        },
                        statistic="Average",
                        period=Duration.minutes(1),
                        label=label,
                    )
                    for metric_name, label in [
                        ("SelectLatency", "Select"),
                        ("InsertLatency", "Insert"),
                        ("UpdateLatency", "Update"),
                        ("DeleteLatency", "Delete"),
                    ]
                ],
                width=8,
            ),
        )

        # == CloudTrail =========================================================
        trail_bucket = s3.Bucket(
            self,
            "TrailBucket",
            bucket_name=f"openmedrecord-{stage}-cloudtrail-{self.account}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(90),
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(365),
                        ),
                    ],
                    # HIPAA requires 6-year retention for audit logs
                    expiration=Duration.days(2190),
                ),
            ],
        )

        trail_log_group = logs.LogGroup(
            self,
            "TrailLogGroup",
            log_group_name=f"/openmedrecord/{stage}/cloudtrail",
            retention=logs.RetentionDays.TWO_YEARS,
        )

        self.trail = cloudtrail.Trail(
            self,
            "CloudTrail",
            trail_name=f"openmedrecord-{stage}",
            bucket=trail_bucket,
            cloud_watch_logs_group=trail_log_group,
            send_to_cloud_watch_logs=True,
            enable_file_validation=True,
            include_global_service_events=True,
            is_multi_region_trail=is_prod,
        )

        # Log all data events for S3 and DynamoDB (PHI stores)
        self.trail.add_s3_event_selector(
            [cloudtrail.S3EventSelector(bucket=trail_bucket)],
            read_write_type=cloudtrail.ReadWriteType.ALL,
            include_management_events=True,
        )

        # == Outputs ============================================================
        CfnOutput(
            self, "DashboardUrl",
            value=(
                f"https://{self.region}.console.aws.amazon.com/cloudwatch/"
                f"home?region={self.region}#dashboards:name="
                f"OpenMedRecord-{stage}"
            ),
        )
        CfnOutput(
            self, "CriticalTopicArn", value=self.critical_topic.topic_arn
        )
        CfnOutput(
            self, "WarningTopicArn", value=self.warning_topic.topic_arn
        )
