from aws_cdk import (
    Stack,
    aws_bedrockagentcore as bedrockagentcore,
    aws_iam as iam,
)
from constructs import Construct


class AgentCoreRuntime(Construct):
    def __init__(self, scope: Construct, construct_id: str, app_name: str, env_name: str,
                 image_uri: str, agent_role: iam.Role, environment_variables: dict = None):
        super().__init__(scope, construct_id)

        stack = Stack.of(self)
        
        # Merge default and custom environment variables
        env_vars = {
            "AWS_DEFAULT_REGION": stack.region
        }
        if environment_variables:
            env_vars.update(environment_variables)

        # Create AgentCore Runtime
        self.runtime = bedrockagentcore.CfnRuntime(self, "Runtime",
            agent_runtime_name=f"{app_name}_{env_name}_runtime",
            agent_runtime_artifact=bedrockagentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=bedrockagentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=image_uri
                )
            ),
            network_configuration=bedrockagentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC"
            ),
            protocol_configuration="HTTP",
            role_arn=agent_role.role_arn,
            description=f"RLM Agent Runtime for {app_name}-{env_name}",
            environment_variables=env_vars
        )

    @property
    def runtime_arn(self) -> str:
        return self.runtime.attr_agent_runtime_arn

    @property
    def runtime_id(self) -> str:
        return self.runtime.attr_agent_runtime_id
