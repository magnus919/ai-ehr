"""
Frontend Stack -- S3 static hosting, CloudFront CDN, and ACM certificate.

Serves the React SPA through CloudFront with Origin Access Identity for
secure S3 access.  Cache behaviors are tuned for a single-page application
(index.html is never cached; hashed assets are cached aggressively).
"""

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct


class FrontendStack(Stack):
    """Provisions the static-site infrastructure for the OpenMedRecord SPA."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        stage: str,
        domain_name: str,
        api_alb: elbv2.IApplicationLoadBalancer,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._stage = stage
        is_prod = stage == "production"

        # -- S3 Bucket for SPA assets ------------------------------------------
        self.site_bucket = s3.Bucket(
            self,
            "SiteBucket",
            bucket_name=f"openmedrecord-{stage}-frontend-{self.account}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=is_prod,
            removal_policy=(
                RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY
            ),
            auto_delete_objects=not is_prod,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=[f"https://{domain_name}", f"https://*.{domain_name}"],
                    allowed_headers=["*"],
                    max_age=86400,
                )
            ],
        )

        # -- Origin Access Identity --------------------------------------------
        oai = cloudfront.OriginAccessIdentity(
            self,
            "OAI",
            comment=f"OAI for OpenMedRecord {stage} frontend",
        )
        self.site_bucket.grant_read(oai)

        # -- Response Headers Policy -------------------------------------------
        response_headers_policy = cloudfront.ResponseHeadersPolicy(
            self,
            "SecurityHeaders",
            response_headers_policy_name=f"omr-{stage}-security-headers",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                content_security_policy=cloudfront.ResponseHeadersContentSecurityPolicy(
                    content_security_policy=(
                        "default-src 'self'; "
                        "script-src 'self'; "
                        "style-src 'self' 'unsafe-inline'; "
                        "img-src 'self' data: blob:; "
                        "font-src 'self'; "
                        f"connect-src 'self' https://api.{domain_name}; "
                        "frame-ancestors 'none'; "
                        "base-uri 'self'; "
                        "form-action 'self'"
                    ),
                    override=True,
                ),
                content_type_options=cloudfront.ResponseHeadersContentTypeOptions(
                    override=True,
                ),
                frame_options=cloudfront.ResponseHeadersFrameOptions(
                    frame_option=cloudfront.HeadersFrameOption.DENY,
                    override=True,
                ),
                referrer_policy=cloudfront.ResponseHeadersReferrerPolicy(
                    referrer_policy=cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
                    override=True,
                ),
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.days(365),
                    include_subdomains=True,
                    preload=True,
                    override=True,
                ),
                xss_protection=cloudfront.ResponseHeadersXSSProtection(
                    protection=True,
                    mode_block=True,
                    override=True,
                ),
            ),
        )

        # -- CloudFront Distribution -------------------------------------------
        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            comment=f"OpenMedRecord {stage} frontend",
            default_root_object="index.html",
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            http_version=cloudfront.HttpVersion.HTTP2_AND_3,
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            # S3 origin for static assets
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.site_bucket,
                    origin_access_identity=oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=response_headers_policy,
                compress=True,
            ),
            additional_behaviors={
                # API calls proxied to ALB
                "/api/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        api_alb.load_balancer_dns_name,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                ),
                "/auth/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        api_alb.load_balancer_dns_name,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                ),
                "/fhir/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        api_alb.load_balancer_dns_name,
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                ),
            },
            # SPA fallback: serve index.html for all unmatched routes
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
            ],
        )

        # -- Outputs ------------------------------------------------------------
        CfnOutput(self, "BucketName", value=self.site_bucket.bucket_name)
        CfnOutput(
            self,
            "DistributionDomainName",
            value=self.distribution.distribution_domain_name,
        )
        CfnOutput(
            self,
            "DistributionId",
            value=self.distribution.distribution_id,
        )
