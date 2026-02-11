"""
VPC Stack -- Network foundation for OpenMedRecord.

Creates a three-AZ VPC with public, private, and isolated (data) subnets.
NAT gateways provide outbound internet access for private subnets.
VPC endpoints keep traffic to AWS services on the private network.
"""

from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class VpcStack(Stack):
    """Provisions the VPC, subnets, NAT gateways, and VPC endpoints."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        stage: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._stage = stage

        # -- VPC ----------------------------------------------------------------
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=f"openmedrecord-{stage}",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,
            nat_gateways=2 if stage == "production" else 1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    map_public_ip_on_launch=False,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Data",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
            restrict_default_security_group=True,
        )

        # -- Flow Logs (HIPAA requirement) --------------------------------------
        self.vpc.add_flow_log(
            "FlowLogCloudWatch",
            traffic_type=ec2.FlowLogTrafficType.ALL,
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(),
        )

        # -- VPC Endpoints (keep traffic off the public internet) ---------------
        self._add_gateway_endpoints()
        self._add_interface_endpoints()

        # -- Outputs ------------------------------------------------------------
        CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join(
                [s.subnet_id for s in self.vpc.private_subnets]
            ),
        )
        CfnOutput(
            self,
            "DataSubnetIds",
            value=",".join(
                [s.subnet_id for s in self.vpc.isolated_subnets]
            ),
        )

    # ------------------------------------------------------------------
    # Gateway endpoints (free, no ENI cost)
    # ------------------------------------------------------------------
    def _add_gateway_endpoints(self) -> None:
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )
        self.vpc.add_gateway_endpoint(
            "DynamoDBEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
        )

    # ------------------------------------------------------------------
    # Interface endpoints (ENI-based, billed per hour + data)
    # ------------------------------------------------------------------
    def _add_interface_endpoints(self) -> None:
        interface_services = {
            "ECRApi": ec2.InterfaceVpcEndpointAwsService.ECR,
            "ECRDocker": ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            "CloudWatchLogs": ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            "CloudWatchMonitoring": ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_MONITORING,
            "SecretsManager": ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            "KMS": ec2.InterfaceVpcEndpointAwsService.KMS,
            "STS": ec2.InterfaceVpcEndpointAwsService.STS,
            "SQS": ec2.InterfaceVpcEndpointAwsService.SQS,
        }

        for name, service in interface_services.items():
            self.vpc.add_interface_endpoint(
                name,
                service=service,
                private_dns_enabled=True,
                subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                ),
            )
