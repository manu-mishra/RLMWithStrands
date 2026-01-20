#!/usr/bin/env python3
"""Run RLM experiments locally with Docker"""
import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and stream output"""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def main():
    project_root = Path(__file__).parent.parent
    
    print("🔨 Building Docker image...")
    run_command(
        ["docker", "build", "--platform", "linux/arm64", "-t", "rlm-local", "."],
        cwd=project_root / "app"
    )
    
    print("🧹 Cleaning up old container...")
    subprocess.run(["docker", "rm", "-f", "rlm-local"], capture_output=True)
    
    print("🚀 Starting container...")
    run_command([
        "docker", "run", "-d",
        "--name", "rlm-local",
        "-p", "8080:8080",
        "-v", f"{Path.home()}/.aws:/home/agentcore/.aws:ro",
        "-e", "AWS_DEFAULT_REGION=us-east-1",
        "-e", "S3_RESULTS_BUCKET=rlm-dev-resultsbucket260a22ad-jvcdcd4jjonb",
        "rlm-local"
    ])
    
    print("⏳ Waiting for container to be ready...")
    time.sleep(5)
    
    print("\n✅ Container running on http://localhost:8080")
    print("\nTest with:")
    print("  python local_testing/test.py s-niah-50k")
    print("\nView logs:")
    print("  docker logs -f rlm-local")
    print("\nStop container:")
    print("  docker stop rlm-local && docker rm rlm-local")

if __name__ == "__main__":
    main()
