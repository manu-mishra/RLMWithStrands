from pathlib import Path

from aws_cdk import (
    Stack,
    CfnOutput,
    Tags,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct
from cdk_constructs.ecr_image import ECRImage
from cdk_constructs.agentcore_role import AgentCoreRole
from cdk_constructs.agentcore_runtime import AgentCoreRuntime
from cdk_constructs.log_group import LogGroup
from cdk_constructs.results_bucket import ResultsBucket


class RLMStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.app_name = config["app_name"]
        self.env_name = config["environment"]

        # S3 bucket for benchmark results
        results_bucket = ResultsBucket(self, "ResultsBucket",
            app_name=self.app_name,
            env_name=self.env_name
        )

        # CloudWatch Log Group
        log_group = LogGroup(self, "LogGroup",
            app_name=self.app_name,
            env_name=self.env_name
        )

        # Build and push Docker image
        image = ECRImage(self, "Image", 
            app_name=self.app_name,
            env_name=self.env_name,
            source_path="../app"
        )

        # Deploy static dataset assets to S3
        datasets_dir = Path(__file__).resolve().parent.parent / "assets" / "datasets"
        if datasets_dir.exists():
            s3deploy.BucketDeployment(self, "DatasetDeployment",
                destination_bucket=results_bucket.bucket,
                destination_key_prefix="datasets",
                sources=[s3deploy.Source.asset(str(datasets_dir))],
                memory_limit=2048  # 2GB for large datasets
            )

        # AgentCore Role
        agent_role = AgentCoreRole(self, "AgentRole")
        
        # Grant S3 permissions to agent role
        results_bucket.bucket.grant_read_write(agent_role.role)

        # AgentCore Runtime
        runtime = AgentCoreRuntime(self, "Runtime",
            app_name=self.app_name,
            env_name=self.env_name,
            image_uri=image.image_uri,
            agent_role=agent_role.role,
            environment_variables={
                "S3_RESULTS_BUCKET": results_bucket.bucket_name,
                "DATASET_PREFIX": "datasets"
            }
        )

        # Ensure log group is created before runtime
        runtime.node.add_dependency(log_group.log_group)
        
        # Tags
        Tags.of(self).add("Project", "RLM")
        Tags.of(self).add("Environment", self.env_name)
        Tags.of(self).add("ManagedBy", "CDK")

        # Outputs
        CfnOutput(self, "RuntimeArn",
            value=runtime.runtime_arn,
            description="AgentCore Runtime ARN"
        )

        CfnOutput(self, "RuntimeId",
            value=runtime.runtime_id,
            description="AgentCore Runtime ID"
        )

        CfnOutput(self, "ResultsBucketName",
            value=results_bucket.bucket_name,
            description="S3 bucket for benchmark results"
        )

        CfnOutput(self, "ImageUri",
            value=image.image_uri,
            description="Docker Image URI"
        )

        CfnOutput(self, "LogGroupName",
            value=log_group.log_group_name,
            description="CloudWatch Log Group Name"
        )
