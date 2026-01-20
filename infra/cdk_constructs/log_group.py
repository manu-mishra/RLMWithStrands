from aws_cdk import (
    RemovalPolicy,
    aws_logs as logs,
)
from constructs import Construct


class LogGroup(Construct):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, env_name: str):
        super().__init__(scope, construct_id)

        self.log_group = logs.LogGroup(self, "LogGroup",
            log_group_name=f"/aws/bedrock-agentcore/runtimes/{app_name}-{env_name}",
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY
        )

    @property
    def log_group_name(self) -> str:
        return self.log_group.log_group_name
