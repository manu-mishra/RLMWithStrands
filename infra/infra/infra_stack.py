from aws_cdk import Stack
from constructs import Construct


class InfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.app_name = config["app_name"]
        self.env_name = config["environment"]

        # Add your infrastructure resources here
