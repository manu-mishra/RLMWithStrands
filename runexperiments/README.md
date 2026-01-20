# Run Experiments

Professional CLI tool to run RLM benchmarks with model selection.

## Structure

```
runexperiments/
├── __main__.py      # Entry point
├── cli.py           # Command-line interface
├── runner.py        # Benchmark orchestration
├── client.py        # AgentCore client
├── display.py       # Terminal output formatting
└── config.py        # Configuration and models
```

## Usage

```bash
# Run all benchmarks (default: Nova Pro + Micro)
python runexperiments

# Run single experiment
python runexperiments s-niah-50k

# Select different model
python runexperiments --model claude-sonnet
python runexperiments --model nova-lite

# Combine experiment + model
python runexperiments s-niah-50k --model claude-sonnet

# Show help
python runexperiments --help
```

## Available Models

- `nova-pro` - Nova Pro + Micro (default)
- `nova-lite` - Nova Lite + Micro (faster)
- `claude-sonnet` - Claude Sonnet + Haiku

## Available Experiments

- `s-niah-50k` - Single needle in 50K haystack
- `s-niah-200k` - Single needle in 200K haystack
- `oolong-100k` - Count aggregation in 100K context
- `multi-needle-150k` - Find 3 needles in 150K context
