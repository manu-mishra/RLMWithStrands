"""Deployment utilities for AgentCore and local Docker"""
import subprocess
import socket
import json
import os
from pathlib import Path
from .display import print_progress, print_success, print_error, print_info, Colors

CONFIG_FILE = Path.home() / ".rlm_config.json"

def load_config():
    """Load saved configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, indent=2, fp=f)

def is_port_available(port):
    """Check if port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except OSError:
        return False

def find_available_port(start=8080, max_attempts=10):
    """Find next available port"""
    for port in range(start, start + max_attempts):
        if is_port_available(port):
            return port
    return None

def deploy_agentcore():
    """Deploy to AgentCore using CDK"""
    print_progress("Deploying to AgentCore...")
    print_info("This may take 5-10 minutes...\n")
    
    # Check if infra directory exists
    if not os.path.exists("infra"):
        print_error("infra/ directory not found. Please run from project root.")
        return False
    
    # Check if venv exists
    venv_path = Path(".venv/bin/activate")
    if not venv_path.exists():
        print_error("Virtual environment not found at .venv/")
        print_info("Please create venv: python3 -m venv .venv && source .venv/bin/activate && pip install -r infra/requirements.txt")
        return False
    
    try:
        # Run CDK deploy with venv activated
        print_info("Running: cdk deploy --require-approval never\n")
        
        # Use bash to source venv and run cdk
        cmd = f"source {venv_path} && cd infra && cdk deploy --require-approval never"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        runtime_arn = None
        
        # Stream output in real-time
        for line in process.stdout:
            print(line, end='')
            output_lines.append(line)
            
            # Extract outputs
            if 'RuntimeArn' in line and 'arn:aws:bedrock-agentcore' in line:
                parts = line.split('=')
                if len(parts) > 1:
                    runtime_arn = parts[-1].strip()
            
            if 'ResultsBucketName' in line:
                parts = line.split('=')
                if len(parts) > 1:
                    bucket_name = parts[-1].strip()
        
        # Wait for completion
        return_code = process.wait()
        
        if return_code != 0:
            print_error(f"\nCDK deploy failed with exit code {return_code}")
            print_error("Common issues:")
            print_error("  - AWS credentials not configured")
            print_error("  - CDK not bootstrapped (run: cdk bootstrap)")
            print_error("  - Missing permissions")
            print_error("  - Docker not running")
            return False
        
        if not runtime_arn:
            print_error("\nDeployment succeeded but could not find RuntimeArn in output")
            print_info("Please check CDK outputs manually")
            return False
        
        # Save configuration
        config = load_config()
        config['runtime_arn'] = runtime_arn
        config['target'] = 'agentcore'
        if 'bucket_name' in locals():
            config['s3_bucket'] = bucket_name
        save_config(config)
        
        print_success(f"\nDeployed successfully!")
        print_info(f"Runtime ARN: {runtime_arn}")
        if 'bucket_name' in locals():
            print_info(f"S3 Bucket: {bucket_name}")
        print()
        
        return True
        
    except FileNotFoundError:
        print_error("CDK not found. Please install: npm install -g aws-cdk")
        return False
    except Exception as e:
        print_error(f"Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_local_docker():
    """Start local Docker container"""
    print_progress("Starting local Docker container...")
    
    # Find available port
    port = find_available_port()
    if not port:
        print_error("No available ports found (tried 8080-8089)")
        return False
    
    if port != 8080:
        print_info(f"Port 8080 in use, using port {port} instead")
    
    try:
        # Check if container already running
        check = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=rlm-benchmark"],
            capture_output=True,
            text=True
        )
        
        if check.stdout.strip():
            print_info("Container already running, stopping it...")
            subprocess.run(["docker", "stop", "rlm-benchmark"], check=True)
            subprocess.run(["docker", "rm", "rlm-benchmark"], check=True)
        
        # Build image
        print_progress("Building Docker image...")
        build = subprocess.run(
            ["docker", "build", "--platform", "linux/arm64", "-t", "rlm-benchmark", "."],
            cwd="app",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if build.returncode != 0:
            print_error(f"Docker build failed: {build.stderr}")
            return False
        
        # Start container
        print_progress(f"Starting container on port {port}...")
        run = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", "rlm-benchmark",
                "-p", f"{port}:8080",
                "-v", f"{Path.home()}/.aws:/home/agentcore/.aws:ro",
                "-e", "AWS_DEFAULT_REGION=us-east-1",
                "-e", "S3_RESULTS_BUCKET=rlm-dev-resultsbucket260a22ad-jvcdcd4jjonb",
                "rlm-benchmark"
            ],
            capture_output=True,
            text=True
        )
        
        if run.returncode != 0:
            print_error(f"Docker run failed: {run.stderr}")
            return False
        
        # Save configuration
        config = load_config()
        config['local_endpoint'] = f"http://localhost:{port}/invocations"
        config['target'] = 'local'
        config['container_name'] = 'rlm-benchmark'
        save_config(config)
        
        print_success(f"Container started on port {port}!")
        print_info(f"Endpoint: http://localhost:{port}/invocations\n")
        
        return True
        
    except subprocess.TimeoutExpired:
        print_error("Docker build timed out")
        return False
    except Exception as e:
        print_error(f"Failed to start Docker: {e}")
        return False

def stop_local_docker():
    """Stop local Docker container"""
    config = load_config()
    container_name = config.get('container_name')
    
    # Try configured name first
    if container_name:
        result = subprocess.run(["docker", "stop", container_name], capture_output=True, text=True)
        if result.returncode == 0:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            print_success(f"Stopped container: {container_name}")
            return True
    
    # If that failed, find any rlm container
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=rlm", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    containers = [c for c in result.stdout.strip().split('\n') if c]
    
    if not containers:
        print_error("No RLM containers found")
        return False
    
    # Stop all found containers
    for container in containers:
        subprocess.run(["docker", "stop", container], capture_output=True)
        print_success(f"Stopped container: {container}")
    
    # Remove config
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    
    return True
