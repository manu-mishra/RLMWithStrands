from aws_cdk import (
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct


class ECRImage(Construct):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, env_name: str, source_path: str):
        super().__init__(scope, construct_id)

        # AgentCore requires ARM64 (AWS Graviton)
        self.image = ecr_assets.DockerImageAsset(self, "Image",
            directory=source_path,
            platform=ecr_assets.Platform.LINUX_ARM64
        )

    @property
    def image_uri(self) -> str:
        return self.image.image_uri
