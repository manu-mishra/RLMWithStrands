# Local Testing

Python scripts for running and testing RLM experiments locally with Docker.

## Quick Start

```bash
# Start local Docker container
python local_testing/run.py

# Test an experiment
python local_testing/test.py s-niah-50k

# View logs
docker logs -f rlm-local

# Stop container
docker stop rlm-local && docker rm rlm-local
```

## Available Experiments

- `s-niah-50k` - 50K token needle-in-haystack
- `s-niah-200k` - 200K token needle-in-haystack
- `s-niah-1m` - 1M token needle-in-haystack
- `oolong` - TREC label counting
- `oolong-pairs` - TREC pair filtering
- `browsecomp-1k` - BrowseComp+ document retrieval
- `codeqa` - Code repository reasoning

## Scripts

- **run.py** - Builds Docker image and starts container
- **test.py** - Invokes experiments and polls for results

## Requirements

- Python 3.10+
- Docker with ARM64 support
- AWS credentials configured (`~/.aws/credentials`)
- S3 bucket with datasets deployed (run `cdk deploy` first)
- `requests` library (`pip install requests`)

## How It Works

1. Container mounts AWS credentials from `~/.aws`
2. Downloads datasets from S3 on first use (cached in `/tmp/rlm_datasets`)
3. Uses AWS credentials for Bedrock API calls
4. Saves results to S3
