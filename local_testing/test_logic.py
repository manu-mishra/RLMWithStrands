#!/usr/bin/env python3
"""Test benchmark agent locally without Docker or AgentCore"""
import sys
from pathlib import Path

# Add app/src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "src"))

from benchmark_agent import execute_benchmark

def test_oolong():
    """Test OOLONG experiment"""
    print("Testing OOLONG (TREC label counting)...")
    
    result = execute_benchmark(
        experiment_name="oolong",
        model_name="openai.gpt-oss-120b-1:0",
        sub_model_name="openai.gpt-oss-20b-1:0",
        session_id="test-session"
    )
    
    print(f"\nResult:")
    print(f"  Passed: {result['passed']}")
    print(f"  Time: {result['elapsed_seconds']}s")
    if 'context_stats' in result:
        print(f"  Context: {result['context_stats']}")
    
    if result['passed']:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        if 'validation_reason' in result:
            print(f"  Reason: {result['validation_reason']}")
        if 'output' in result:
            print(f"  Output: {result['output']}")
        if 'expected' in result:
            print(f"  Expected: {result['expected']}")
    
    if 'error' in result:
        print(f"  Error: {result['error']}")

def test_codeqa():
    """Test CodeQA experiment"""
    print("\nTesting CodeQA...")
    
    result = execute_benchmark(
        experiment_name="codeqa",
        model_name="openai.gpt-oss-120b-1:0",
        sub_model_name="openai.gpt-oss-20b-1:0",
        session_id="test-session"
    )
    
    print(f"\nResult:")
    print(f"  Passed: {result['passed']}")
    print(f"  Time: {result['elapsed_seconds']}s")
    
    if result['passed']:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
        if 'validation_reason' in result:
            print(f"  Reason: {result['validation_reason']}")
        if 'output' in result:
            print(f"  Output: {result['output']}")
        if 'expected' in result:
            print(f"  Expected: {result['expected']}")
    
    if 'error' in result:
        print(f"  Error: {result['error']}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", nargs="?", default="oolong", 
                       choices=["oolong", "oolong-pairs", "browsecomp-1k", "codeqa"])
    args = parser.parse_args()
    
    if args.experiment == "oolong":
        test_oolong()
    elif args.experiment == "codeqa":
        test_codeqa()
    else:
        print(f"Testing {args.experiment}...")
        result = execute_benchmark(
            experiment_name=args.experiment,
            model_name="openai.gpt-oss-120b-1:0",
            sub_model_name="openai.gpt-oss-20b-1:0",
            session_id="test-session"
        )
        print(f"Passed: {result['passed']}")
        if not result['passed']:
            if 'validation_reason' in result:
                print(f"Reason: {result['validation_reason']}")
            if 'output' in result:
                print(f"Output: {result['output']}")
            if 'expected' in result:
                print(f"Expected: {result['expected']}")
        if 'error' in result:
            print(f"Error: {result['error']}")
