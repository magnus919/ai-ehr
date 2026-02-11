"""
Compute Stack -- ECS Fargate cluster, task definitions, ALB, and auto-scaling.

Runs the OpenMedRecord backend micro-services on AWS Fargate behind an
Application Load Balancer with HTTPS termination.
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class ComputeStack(Stack):
    """Provisions ECS Fargate services and the application load balancer."""

    # Services and their path-based routing rules
    SERVICE_CONFIG = {
        "api-gateway": {
            "path_pattern": "/api/v1/*",
            "priority": 100,
            "port": 8000,
            "cpu": 512,
            "memory": 1024,
            "desired_count": 2,
            "health_check_path": "/api/v1/health",
        },
        "auth-service": {
            "path_pattern": "/auth/*",
            "priority": 110,
            "port": 8000,
            "cpu": 512,
            "memory": 1024,
            "desired_count": 2,
            "health_check_path": "/auth/health",
        },
        "fhir-gateway": {
            "path_pattern": "/fhir/*",
            "priority": 120,
            "port": 8000,
            "cpu": 1024,
            "memory": 2048,
            "desired_count": 2,
            "health_check_path": "/fhir/metadata",
        },
    }

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        stage: str,
        vpc: ec2.IVpc,
        cluster_security_group: ec2.ISecurityGroup,
        db_secret: secretsmanager.ISecret,
        redis_endpoint: str,
        kms_key: kms.IKey,
        domain_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._stage = stage
        self._vpc = vpc
        is_prod = stage == "production"

        # -- ECR Repositories ---------------------------------------------------
        self._repositories: dict[str, ecr.IRepository] = {}
        for svc_name in self.SERVICE_CONFIG:
            repo = ecr.Repository(
                self,
                f"Repo-{svc_name}",
                repository_name=f"openmedrecord/{svc_name}",
                image_scan_on_push=True,
                encryption=ecr.RepositoryEncryption.KMS,
                encryption_key=kms_key,
            )
            self._repositories[svc_name] = repo

        # -- ECS Cluster --------------------------------------------------------
        self.cluster = ecs.Cluster(
            self,
            "EcsCluster",
            cluster_name=f"openmedrecord-{stage}",
            vpc=vpc,
            container_insights=True,
            enable_fargate_capacity_providers=True,
        )

        # -- Application Load Balancer ------------------------------------------
        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            "ALB",
            load_balancer_name=f"omr-{stage}",
            vpc=vpc,
            internet_facing=True,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            drop_invalid_header_fields=True,
        )

        # HTTPS listener (port 443)
        self._https_listener = self.alb.add_listener(
            "HttpsListener",
            port=443,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            ssl_policy=elbv2.SslPolicy.TLS13_13,
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="application/json",
                message_body='{"error": "not_found"}',
            ),
        )

        # HTTP -> HTTPS redirect
        self.alb.add_listener(
            "HttpRedirect",
            port=80,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True,
            ),
        )

        # -- Task Execution Role ------------------------------------------------
        execution_role = iam.Role(
            self,
            "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                ),
            ],
        )
        db_secret.grant_read(execution_role)
        kms_key.grant_decrypt(execution_role)

        # -- Task Role (permissions for the running containers) -----------------
        task_role = iam.Role(
            self,
            "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        kms_key.grant_encrypt_decrypt(task_role)
        db_secret.grant_read(task_role)

        # -- Log Group ----------------------------------------------------------
        log_group = logs.LogGroup(
            self,
            "ServiceLogs",
            log_group_name=f"/openmedrecord/{stage}/ecs",
            retention=logs.RetentionDays.ONE_YEAR if is_prod else logs.RetentionDays.ONE_MONTH,
        )

        # -- Deploy each service ------------------------------------------------
        self._services: dict[str, ecs.FargateService] = {}

        for svc_name, cfg in self.SERVICE_CONFIG.items():
            service = self._create_fargate_service(
                svc_name=svc_name,
                cfg=cfg,
                stage=stage,
                is_prod=is_prod,
                execution_role=execution_role,
                task_role=task_role,
                log_group=log_group,
                db_secret=db_secret,
                redis_endpoint=redis_endpoint,
                cluster_security_group=cluster_security_group,
            )
            self._services[svc_name] = service

        # -- Outputs ------------------------------------------------------------
        CfnOutput(self, "ClusterArn", value=self.cluster.cluster_arn)
        CfnOutput(self, "ALBDnsName", value=self.alb.load_balancer_dns_name)

    def _create_fargate_service(
        self,
        *,
        svc_name: str,
        cfg: dict,
        stage: str,
        is_prod: bool,
        execution_role: iam.IRole,
        task_role: iam.IRole,
        log_group: logs.ILogGroup,
        db_secret: secretsmanager.ISecret,
        redis_endpoint: str,
        cluster_security_group: ec2.ISecurityGroup,
    ) -> ecs.FargateService:
        """Create a Fargate service with target group and auto-scaling."""

        task_definition = ecs.FargateTaskDefinition(
            self,
            f"TaskDef-{svc_name}",
            family=f"openmedrecord-{stage}-{svc_name}",
            cpu=cfg["cpu"],
            memory_limit_mib=cfg["memory"],
            execution_role=execution_role,
            task_role=task_role,
        )

        container = task_definition.add_container(
            f"Container-{svc_name}",
            container_name=svc_name,
            image=ecs.ContainerImage.from_ecr_repository(
                self._repositories[svc_name],
                tag="latest",
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix=svc_name,
                log_group=log_group,
            ),
            environment={
                "ENVIRONMENT": stage,
                "SERVICE_NAME": svc_name,
                "LOG_LEVEL": "INFO" if is_prod else "DEBUG",
                "LOG_FORMAT": "json",
                "REDIS_URL": f"rediss://{redis_endpoint}:6379/0",
            },
            secrets={
                "DATABASE_URL": ecs.Secret.from_secrets_manager(
                    db_secret, "connection_string"
                ),
                "JWT_SECRET_KEY": ecs.Secret.from_secrets_manager(
                    db_secret, "jwt_secret"
                ),
            },
            health_check=ecs.HealthCheck(
                command=[
                    "CMD-SHELL",
                    f"curl -f http://localhost:{cfg['port']}{cfg['health_check_path']} || exit 1",
                ],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60),
            ),
        )

        container.add_port_mappings(
            ecs.PortMapping(
                container_port=cfg["port"],
                protocol=ecs.Protocol.TCP,
            )
        )

        service = ecs.FargateService(
            self,
            f"Service-{svc_name}",
            service_name=f"omr-{stage}-{svc_name}",
            cluster=self.cluster,
            task_definition=task_definition,
            desired_count=cfg["desired_count"] if is_prod else 1,
            security_groups=[cluster_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            assign_public_ip=False,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            min_healthy_percent=100 if is_prod else 50,
            max_healthy_percent=200,
            enable_execute_command=not is_prod,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE",
                    weight=1 if is_prod else 0,
                ),
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE_SPOT",
                    weight=0 if is_prod else 1,
                ),
            ],
        )

        # Target group
        target_group = elbv2.ApplicationTargetGroup(
            self,
            f"TG-{svc_name}",
            target_group_name=f"omr-{stage}-{svc_name}"[:32],
            vpc=self._vpc,
            port=cfg["port"],
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path=cfg["health_check_path"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(10),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
                healthy_http_codes="200",
            ),
            deregistration_delay=Duration.seconds(30),
        )
        target_group.add_target(service)

        # Listener rule
        elbv2.ApplicationListenerRule(
            self,
            f"Rule-{svc_name}",
            listener=self._https_listener,
            priority=cfg["priority"],
            conditions=[
                elbv2.ListenerCondition.path_patterns([cfg["path_pattern"]]),
            ],
            target_groups=[target_group],
        )

        # Auto-scaling
        scaling = service.auto_scale_task_count(
            min_capacity=cfg["desired_count"] if is_prod else 1,
            max_capacity=cfg["desired_count"] * 4 if is_prod else 2,
        )

        scaling.scale_on_cpu_utilization(
            f"CpuScaling-{svc_name}",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(60),
        )

        scaling.scale_on_memory_utilization(
            f"MemScaling-{svc_name}",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(60),
        )

        scaling.scale_on_request_count(
            f"RequestScaling-{svc_name}",
            requests_per_target=1000,
            target_group=target_group,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(60),
        )

        return service
