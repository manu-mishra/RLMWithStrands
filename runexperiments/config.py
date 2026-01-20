"""Configuration for RLM benchmarks"""

RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:878004393455:runtime/rlm_dev_runtime-kVhLCmGRGO"
REGION = "us-east-1"
LOCAL_ENDPOINT = "http://localhost:8080/invocations"

# Available model configurations
MODELS = {
    "nova-premier": {
        "root": "amazon.nova-premier-v1:0",
        "sub": "amazon.nova-micro-v1:0",
        "description": "Nova Premier + Micro (highest quality)"
    },
    "nova-pro": {
        "root": "amazon.nova-pro-v1:0",
        "sub": "amazon.nova-micro-v1:0",
        "description": "Nova Pro + Micro (balanced)"
    },
    "nova-lite": {
        "root": "amazon.nova-lite-v1:0",
        "sub": "amazon.nova-micro-v1:0",
        "description": "Nova Lite + Micro (fast)"
    },
    "claude-opus": {
        "root": "anthropic.claude-opus-4-5-20251101-v1:0",
        "sub": "anthropic.claude-haiku-4-5-20251001-v1:0",
        "description": "Claude Opus 4.5 + Haiku 4.5"
    },
    "claude-sonnet": {
        "root": "anthropic.claude-sonnet-4-5-20250929-v1:0",
        "sub": "anthropic.claude-haiku-4-5-20251001-v1:0",
        "description": "Claude Sonnet 4.5 + Haiku 4.5"
    },
    "gpt-oss-120b": {
        "root": "openai.gpt-oss-120b-1:0",
        "sub": "openai.gpt-oss-20b-1:0",
        "description": "GPT-OSS 120B + 20B (OpenAI open-weight)"
    },
    "deepseek-r1": {
        "root": "deepseek.r1-v1:0",
        "sub": "deepseek.v3-v1:0",
        "description": "DeepSeek R1 + V3 (reasoning)"
    }
}

# Benchmark experiments
EXPERIMENTS = {
    "oolong": {
        "name": "OOLONG (TREC coarse)",
        "description": "Aggregate label stats across the full TREC coarse dataset"
    },
    "oolong-pairs": {
        "name": "OOLONG-Pairs (TREC coarse)",
        "description": "Enumerate HUM/LOC question ID pairs with semantic filters"
    },
    "browsecomp-1k": {
        "name": "BrowseComp+ (1K docs)",
        "description": "Streaming 1000-document retrieval task from Tevatron corpus"
    },
    "codeqa": {
        "name": "LongBench CodeQA",
        "description": "LongBench-v2 code repository multiple-choice question"
    }
}
