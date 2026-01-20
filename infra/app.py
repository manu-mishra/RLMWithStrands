#!/usr/bin/env python3
import os
import yaml
import aws_cdk as cdk
from infra.rlm_stack import RLMStack

app = cdk.App()

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

app_name = config["app_name"]
environment = config["environment"]
region = config.get("region", "us-east-1")

# Create stack
RLMStack(
    app,
    f"{app_name}-{environment}",
    config=config,
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=region
    ),
)

app.synth()
