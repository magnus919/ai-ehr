"""
Security Stack -- KMS keys, WAF, Secrets Manager, IAM roles, and security groups.

Implements defense-in-depth for HIPAA-compliant PHI handling:
  - Customer-managed KMS keys for encryption at rest
  - AWS WAF v2 with OWASP Top 10 rule groups
  - Least-privilege IAM roles
  - Network-level isolation via security groups
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_kms as kms,
    aws_secretsmanager as secretsmanager,
    aws_wafv2 as wafv2,
)
from constructs import Construct


class SecurityStack(Stack):
    """Provisions all security primitives consumed by other stacks."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        stage: str,
        vpc: ec2.IVpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._stage = stage
        self._vpc = vpc

        # == KMS Keys ===========================================================
        self.data_key = self._create_data_encryption_key()

        # == Security Groups ====================================================
        self.alb_security_group = self._create_alb_security_group()
        self.ecs_security_group = self._create_ecs_security_group()
        self.db_security_group = self._create_db_security_group()
        self.cache_security_group = self._create_cache_security_group()

        # == WAF ================================================================
        self.web_acl = self._create_waf_web_acl()

        # == Secrets ============================================================
        self._create_application_secrets()

        # == Outputs ============================================================
        CfnOutput(self, "DataKeyArn", value=self.data_key.key_arn)
        CfnOutput(self, "WebAclArn", value=self.web_acl.attr_arn)

    # ------------------------------------------------------------------
    # KMS
    # ------------------------------------------------------------------
    def _create_data_encryption_key(self) -> kms.Key:
        """Customer-managed KMS key for encrypting all PHI at rest."""
        return kms.Key(
            self,
            "DataEncryptionKey",
            alias=f"openmedrecord/{self._stage}/data",
            description="Encrypts PHI data at rest (Aurora, DynamoDB, ElastiCache, S3)",
            enable_key_rotation=True,
            pending_window=Duration.days(30),
            removal_policy=(
                RemovalPolicy.RETAIN
                if self._stage == "production"
                else RemovalPolicy.DESTROY
            ),
            policy=iam.PolicyDocument(
                statements=[
                    # Allow account root full access (required)
                    iam.PolicyStatement(
                        sid="AllowRootAccess",
                        actions=["kms:*"],
                        resources=["*"],
                        principals=[iam.AccountRootPrincipal()],
                    ),
                    # Allow CloudWatch Logs to use the key
                    iam.PolicyStatement(
                        sid="AllowCloudWatchLogs",
                        actions=[
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey",
                        ],
                        resources=["*"],
                        principals=[
                            iam.ServicePrincipal(
                                f"logs.{self.region}.amazonaws.com"
                            )
                        ],
                        conditions={
                            "ArnLike": {
                                "kms:EncryptionContext:aws:logs:arn": (
                                    f"arn:aws:logs:{self.region}:{self.account}:*"
                                )
                            }
                        },
                    ),
                ]
            ),
        )

    # ------------------------------------------------------------------
    # Security Groups
    # ------------------------------------------------------------------
    def _create_alb_security_group(self) -> ec2.SecurityGroup:
        sg = ec2.SecurityGroup(
            self,
            "AlbSG",
            vpc=self._vpc,
            security_group_name=f"omr-{self._stage}-alb",
            description="ALB - allows inbound HTTPS from internet",
            allow_all_outbound=False,
        )
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "HTTPS")
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP redirect")
        return sg

    def _create_ecs_security_group(self) -> ec2.SecurityGroup:
        sg = ec2.SecurityGroup(
            self,
            "EcsSG",
            vpc=self._vpc,
            security_group_name=f"omr-{self._stage}-ecs",
            description="ECS tasks - allows inbound from ALB only",
            allow_all_outbound=True,
        )
        sg.add_ingress_rule(
            self.alb_security_group,
            ec2.Port.tcp_range(8000, 8099),
            "ALB to ECS services",
        )
        return sg

    def _create_db_security_group(self) -> ec2.SecurityGroup:
        sg = ec2.SecurityGroup(
            self,
            "DbSG",
            vpc=self._vpc,
            security_group_name=f"omr-{self._stage}-aurora",
            description="Aurora - allows inbound from ECS tasks only",
            allow_all_outbound=False,
        )
        sg.add_ingress_rule(
            self.ecs_security_group,
            ec2.Port.tcp(5432),
            "ECS to Aurora PostgreSQL",
        )
        return sg

    def _create_cache_security_group(self) -> ec2.SecurityGroup:
        sg = ec2.SecurityGroup(
            self,
            "CacheSG",
            vpc=self._vpc,
            security_group_name=f"omr-{self._stage}-redis",
            description="Redis - allows inbound from ECS tasks only",
            allow_all_outbound=False,
        )
        sg.add_ingress_rule(
            self.ecs_security_group,
            ec2.Port.tcp(6379),
            "ECS to Redis",
        )
        return sg

    # ------------------------------------------------------------------
    # WAF v2
    # ------------------------------------------------------------------
    def _create_waf_web_acl(self) -> wafv2.CfnWebACL:
        """WAF with AWS Managed Rule Groups covering OWASP Top 10."""
        return wafv2.CfnWebACL(
            self,
            "WebACL",
            name=f"openmedrecord-{self._stage}",
            scope="CLOUDFRONT",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name=f"omr-{self._stage}-waf",
            ),
            rules=[
                # 1. AWS Managed - Common Rule Set (OWASP core)
                self._managed_rule("AWSManagedRulesCommonRuleSet", 1),
                # 2. AWS Managed - Known Bad Inputs
                self._managed_rule("AWSManagedRulesKnownBadInputsRuleSet", 2),
                # 3. AWS Managed - SQL Injection
                self._managed_rule("AWSManagedRulesSQLiRuleSet", 3),
                # 4. AWS Managed - Linux OS (for container-based apps)
                self._managed_rule("AWSManagedRulesLinuxRuleSet", 4),
                # 5. Rate limiting
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimit",
                    priority=10,
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=2000,
                            aggregate_key_type="IP",
                        ),
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="omr-rate-limit",
                    ),
                ),
                # 6. Block requests with bodies over 8KB (unless upload endpoint)
                wafv2.CfnWebACL.RuleProperty(
                    name="SizeRestriction",
                    priority=20,
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        and_statement=wafv2.CfnWebACL.AndStatementProperty(
                            statements=[
                                wafv2.CfnWebACL.StatementProperty(
                                    size_constraint_statement=wafv2.CfnWebACL.SizeConstraintStatementProperty(
                                        field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                                            body=wafv2.CfnWebACL.BodyProperty(
                                                oversize_handling="MATCH",
                                            ),
                                        ),
                                        comparison_operator="GT",
                                        size=8192,
                                        text_transformations=[
                                            wafv2.CfnWebACL.TextTransformationProperty(
                                                priority=0,
                                                type="NONE",
                                            )
                                        ],
                                    ),
                                ),
                                wafv2.CfnWebACL.StatementProperty(
                                    not_statement=wafv2.CfnWebACL.NotStatementProperty(
                                        statement=wafv2.CfnWebACL.StatementProperty(
                                            byte_match_statement=wafv2.CfnWebACL.ByteMatchStatementProperty(
                                                field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                                                    uri_path={},
                                                ),
                                                positional_constraint="STARTS_WITH",
                                                search_string="/api/v1/documents/upload",
                                                text_transformations=[
                                                    wafv2.CfnWebACL.TextTransformationProperty(
                                                        priority=0,
                                                        type="LOWERCASE",
                                                    )
                                                ],
                                            ),
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="omr-size-restriction",
                    ),
                ),
            ],
        )

    @staticmethod
    def _managed_rule(
        name: str, priority: int
    ) -> wafv2.CfnWebACL.RuleProperty:
        """Helper to create an AWS Managed Rule Group reference."""
        return wafv2.CfnWebACL.RuleProperty(
            name=name,
            priority=priority,
            override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
            statement=wafv2.CfnWebACL.StatementProperty(
                managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                    vendor_name="AWS",
                    name=name,
                ),
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name=f"omr-{name}",
            ),
        )

    # ------------------------------------------------------------------
    # Secrets Manager
    # ------------------------------------------------------------------
    def _create_application_secrets(self) -> None:
        """Create placeholder secrets that operators populate post-deploy."""
        secret_definitions = {
            "jwt-secret": "JWT signing secret for access/refresh tokens",
            "field-encryption-key": "Fernet key for PHI field-level encryption",
            "mfa-encryption-key": "Key for encrypting TOTP secrets at rest",
            "smtp-credentials": "SMTP credentials for email notifications",
        }

        for secret_name, description in secret_definitions.items():
            secretsmanager.Secret(
                self,
                f"Secret-{secret_name}",
                secret_name=f"openmedrecord/{self._stage}/{secret_name}",
                description=description,
                encryption_key=self.data_key,
                generate_secret_string=secretsmanager.SecretStringGenerator(
                    password_length=64,
                    exclude_characters="\"@/\\",
                ),
            )
