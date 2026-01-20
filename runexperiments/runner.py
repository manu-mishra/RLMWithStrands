"""Benchmark runner orchestration"""
import uuid
import time
from .config import EXPERIMENTS, MODELS
from .client import BenchmarkClient
from .deploy import load_config
from .display import (
    print_header, print_progress, print_success, print_error, 
    print_info, print_divider, format_status, format_pass_rate, Colors
)

class BenchmarkRunner:
    def __init__(self, model_key="nova-pro"):
        self.client = BenchmarkClient()
        self.model_key = model_key
        self.model_config = MODELS[model_key]
        self.config = load_config()
        self.target = self.config.get('target', 'unknown')
    
    def run_single(self, experiment_id):
        """Run a single experiment (always async)"""
        if experiment_id not in EXPERIMENTS:
            print_error(f"Unknown experiment: {experiment_id}")
            print_info(f"Available: {', '.join(EXPERIMENTS.keys())}")
            return None
        
        exp = EXPERIMENTS[experiment_id]
        session_id = str(uuid.uuid4())
        
        print_header("RLM SINGLE EXPERIMENT")
        print_info(f"Experiment: {Colors.BOLD}{exp['name']}{Colors.END}")
        print_info(f"Model: {Colors.BOLD}{self.model_config['description']}{Colors.END}")
        print_info(f"Target: {Colors.BOLD}{'Local Docker' if self.target == 'local' else 'AgentCore'}{Colors.END}")
        if self.target == 'agentcore' and self.config.get('s3_bucket'):
            print_info(f"S3 Bucket: {Colors.BOLD}{self.config.get('s3_bucket')}{Colors.END}")
        print_info(f"Session: {Colors.BOLD}{session_id[:8]}...{Colors.END}\n")
        
        print_divider()
        print_progress(f"Starting {experiment_id}")
        
        result = self.client.invoke_experiment(
            experiment_id, 
            self.model_config, 
            session_id
        )
        
        # Display result
        if result.get("passed"):
            print_success(f"PASSED in {result.get('elapsed_seconds', 0)}s")
            if result.get('validation_reason'):
                print(f"  {Colors.GREEN}✓{Colors.END} {result.get('validation_reason')}")
        else:
            print_error(f"FAILED in {result.get('elapsed_seconds', 0)}s")
            if result.get('validation_reason'):
                print(f"  {Colors.RED}✗ Reason:{Colors.END} {result.get('validation_reason')}")
            if result.get("error"):
                print(f"  {Colors.RED}Error:{Colors.END} {result.get('error')}")
        
        # Always show full output and expected
        output = result.get("output") or result.get("result")  # Try both keys
        if output:
            print(f"\n  {Colors.YELLOW}Output:{Colors.END}")
            print(f"  {output}")
        if result.get("expected"):
            print(f"\n  {Colors.CYAN}Expected:{Colors.END}")
            print(f"  {result.get('expected')}")
        
        print()
        return result
    
    def run_all(self):
        """Run all experiments (always async)"""
        session_id = str(uuid.uuid4())
        results = []
        
        print_header("RLM BENCHMARK SUITE")
        print_info(f"Running {len(EXPERIMENTS)} experiments")
        print_info(f"Model: {Colors.BOLD}{self.model_config['description']}{Colors.END}")
        print_info(f"Target: {Colors.BOLD}{'Local Docker' if self.target == 'local' else 'AgentCore'}{Colors.END}")
        if self.target == 'agentcore' and self.config.get('s3_bucket'):
            print_info(f"S3 Bucket: {Colors.BOLD}{self.config.get('s3_bucket')}{Colors.END}")
        print_info(f"Session: {Colors.BOLD}{session_id[:8]}...{Colors.END}\n")
        
        for i, (exp_id, exp_info) in enumerate(EXPERIMENTS.items(), 1):
            print(f"\n{Colors.BOLD}[{i}/{len(EXPERIMENTS)}]{Colors.END} {exp_info['name']}")
            print_divider()
            print_progress(f"Starting {exp_id}")
            
            result = self.client.invoke_experiment(
                exp_id,
                self.model_config,
                session_id
            )
            results.append(result)
            
            # Display result
            if result.get("passed"):
                print_success(f"PASSED in {result.get('elapsed_seconds', 0)}s")
                if result.get('validation_reason'):
                    print(f"  {Colors.GREEN}✓{Colors.END} {result.get('validation_reason')}")
            else:
                print_error(f"FAILED in {result.get('elapsed_seconds', 0)}s")
                if result.get('validation_reason'):
                    print(f"  {Colors.RED}✗ Reason:{Colors.END} {result.get('validation_reason')}")
                if result.get("error"):
                    print(f"  {Colors.RED}Error:{Colors.END} {result.get('error')}")
            
            # Debug: show what keys are in result
            if not (result.get("output") or result.get("result")):
                print(f"  {Colors.YELLOW}[Debug] Result keys:{Colors.END} {list(result.keys())}")
            
            # Always show full output and expected
            output = result.get("output") or result.get("result")  # Try both keys
            if output:
                print(f"\n  {Colors.YELLOW}Output:{Colors.END}")
                print(f"  {output}")
            if result.get("expected"):
                print(f"\n  {Colors.CYAN}Expected:{Colors.END}")
                print(f"  {result.get('expected')}")
            
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        self._print_summary(results)
        return results
    
    def _print_summary(self, results):
        """Print results summary table"""
        print_header("RESULTS SUMMARY")
        
        passed = sum(1 for r in results if r.get("passed"))
        total = len(results)
        
        # Table header
        print(f"\n{Colors.BOLD}{'Test':<25} {'Status':<20} {'Time':<10}{Colors.END}")
        print_divider()
        
        # Table rows
        for r in results:
            exp = r.get("experiment", "unknown")
            status = format_status(r.get("passed"))
            elapsed = f"{r.get('elapsed_seconds', 0):.1f}s"
            print(f"{exp:<25} {status:<30} {elapsed:<10}")
        
        print_divider()
        
        # Overall stats
        print(f"\n{Colors.BOLD}Overall:{Colors.END} {format_pass_rate(passed, total)}")
        
        # Show failures in detail
        failures = [r for r in results if not r.get("passed")]
        if failures:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED TESTS:{Colors.END}\n")
            for r in failures:
                print(f"{Colors.BOLD}{r.get('experiment')}:{Colors.END}")
                if r.get("error"):
                    print(f"  {Colors.RED}Error:{Colors.END} {r.get('error')}")
                if r.get("result"):
                    print(f"  {Colors.YELLOW}Got:{Colors.END} {r.get('result')[:300]}...")
                if r.get("expected"):
                    print(f"  {Colors.CYAN}Expected:{Colors.END} {r.get('expected')}")
                print()
