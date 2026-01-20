import os
os.environ['CDK_DEFAULT_ACCOUNT'] = os.popen('aws sts get-caller-identity --query Account --output text').read().strip()
os.environ['CDK_DEFAULT_REGION'] = 'us-east-1'

import sys
sys.path.insert(0, '.')

import aws_cdk as cdk
import yaml
from infra.rlm_stack import RLMStack

with open('config.yaml') as f:
    config = yaml.safe_load(f)

app = cdk.App()
stack = RLMStack(
    app,
    f"{config['app_name']}-{config['environment']}",
    config=config,
    env=cdk.Environment(
        account=os.environ['CDK_DEFAULT_ACCOUNT'],
        region=config['region']
    )
)

# Synthesize
cloud_assembly = app.synth()
print(f"✓ Synthesized to: {cloud_assembly.directory}")
