#!/usr/bin/env python3
"""Run all experiments locally with detailed error reporting"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "src"))

from benchmark_agent import EXPERIMENT_BUILDERS, execute_benchmark
import os

# Set S3 bucket
os.environ['S3_RESULTS_BUCKET'] = 'rlm-dev-resultsbucket260a22ad-jvcdcd4jjonb'

def run_all_experiments():
    """Run all experiments and show detailed results"""
    experiments = list(EXPERIMENT_BUILDERS.keys())
    
    print(f"Running {len(experiments)} experiments with GPT-OSS models...\n")
    
    results = []
    for i, exp_name in enumerate(experiments, 1):
        print(f"[{i}/{len(experiments)}] {exp_name}")
        print("=" * 60)
        
        try:
            result = execute_benchmark(
                experiment_name=exp_name,
                model_name="openai.gpt-oss-120b-1:0",
                sub_model_name="openai.gpt-oss-20b-1:0",
                session_id=f"test-{exp_name}"
            )
            
            results.append((exp_name, result))
            
            # Show result
            if result.get('passed'):
                print(f"✅ PASSED in {result['elapsed_seconds']}s")
                if 'validation_reason' in result:
                    print(f"   {result['validation_reason']}")
            else:
                print(f"❌ FAILED in {result['elapsed_seconds']}s")
                if 'validation_reason' in result:
                    print(f"   Reason: {result['validation_reason']}")
            
            # Show error if present
            if 'error' in result:
                print(f"\nError: {result['error']}")
            
            # For failures, show output vs expected
            if not result.get('passed') and 'error' not in result:
                if 'output' in result:
                    output = result['output']
                    if len(output) > 300:
                        print(f"\nOutput (first 300 chars):\n{output[:300]}...")
                    else:
                        print(f"\nOutput:\n{output}")
                
                if 'expected' in result:
                    expected = str(result['expected'])
                    if len(expected) > 200:
                        print(f"\nExpected (first 200 chars):\n{expected[:200]}...")
                    else:
                        print(f"\nExpected:\n{expected}")
            
        except Exception as e:
            print(f"❌ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((exp_name, {"error": str(e), "passed": False}))
        
        print("\n")
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, r in results if r.get('passed'))
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {len(results) - passed}/{len(results)}")
    print()
    
    for exp_name, result in results:
        status = "✅" if result.get('passed') else "❌"
        time_str = f"{result.get('elapsed_seconds', 0)}s"
        print(f"{status} {exp_name:20s} {time_str:>8s}")

if __name__ == "__main__":
    run_all_experiments()
