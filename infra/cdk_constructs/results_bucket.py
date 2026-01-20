from aws_cdk import (
    RemovalPolicy,
    aws_s3 as s3,
)
from constructs import Construct


class ResultsBucket(Construct):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, env_name: str):
        super().__init__(scope, construct_id)

        # S3 bucket with CDK auto-generated globally unique name
        self.bucket = s3.Bucket(self, "Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED
        )

    @property
    def bucket_name(self) -> str:
        return self.bucket.bucket_name
