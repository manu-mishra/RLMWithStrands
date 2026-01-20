"""Refactored benchmark agent - cleaner, more maintainable

Reduced from ~540 lines to ~250 lines by:
- Extracting dataset loading to datasets.py
- Extracting context building to context_builders.py  
- Extracting configs/validators to experiments.py
- Using factory pattern for payload building
"""
import os
import time
import threading
import random
from dataclasses import dataclass
from typing import Any, Dict, Callable, List
import boto3

from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Handle imports for both local and Docker environments
try:
    from src.rlm_agent import RLMAgent
    from src.datasets import load_trec_entries, load_codeqa_entries, load_browsecomp_sample
    from src.context_builders import (
        build_trec_context,
        build_browsecomp_context,
        build_codeqa_context,
    )
    from src.experiments import (
        validate_needle,
        validate_label_counts,
        validate_id_pairs,
        validate_multiple_choice,
    )
except ImportError:
    from rlm_agent import RLMAgent
    from datasets import load_trec_entries, load_codeqa_entries, load_browsecomp_sample
    from context_builders import (
        build_trec_context,
        build_browsecomp_context,
        build_codeqa_context,
    )
    from experiments import (
        validate_needle,
        validate_label_counts,
        validate_id_pairs,
        validate_multiple_choice,
    )

app = BedrockAgentCoreApp(debug=True)

# S3 for results
s3_client = boto3.client("s3")
S3_BUCKET = os.environ.get("S3_RESULTS_BUCKET", "rlm-benchmark-results-local")

# Async task storage
benchmark_results: Dict[str, Dict[str, Any]] = {}


@dataclass
class ExperimentPayload:
    """Experiment data"""
    name: str
    query: str
    context: Any
    expected: Any
    description: str
    validator: Callable[[str, "ExperimentPayload"], bool]


def session_seed(session_id: str) -> int:
    """Generate deterministic seed from session ID"""
    return hash(session_id) % (2**31)


def context_stats(context: Any) -> Dict[str, int]:
    """Get context statistics"""
    if isinstance(context, str):
        return {"chunks": 1, "characters": len(context)}
    if isinstance(context, list):
        total_chars = sum(len(str(c)) for c in context)
        return {"chunks": len(context), "characters": total_chars}
    return {"chunks": 0, "characters": 0}


# ============================================================================
# Payload Builders
# ============================================================================

def build_oolong_payload() -> ExperimentPayload:
    """Build OOLONG label counting experiment"""
    entries = load_trec_entries()
    context = build_trec_context(entries)
    
    # Count labels
    label_counts = {}
    for entry in entries:
        label = entry["label"]
        label_counts[label] = label_counts.get(label, 0) + 1
    
    query = "Count how many questions belong to each label category (ABBR, ENTY, DESC, HUM, LOC, NUM)."
    
    return ExperimentPayload(
        name="oolong",
        query=query,
        context=context,
        expected=label_counts,
        description="TREC label frequency counting",
        validator=validate_label_counts,
    )


def build_oolong_pairs_payload() -> ExperimentPayload:
    """Build OOLONG pairs experiment"""
    entries = load_trec_entries()
    context = build_trec_context(entries)
    
    # Find HUM/LOC pairs
    hum_entries = [e for e in entries if e["label"] == "HUM"]
    loc_entries = [e for e in entries if e["label"] == "LOC"]
    
    pairs = []
    for h in hum_entries[:10]:
        for l in loc_entries[:10]:
            if "city" in h["text"].lower() and "capital" in l["text"].lower():
                pairs.append((h["id"], l["id"]))
                if len(pairs) >= 5:
                    break
        if len(pairs) >= 5:
            break
    
    query = 'List pairs of question IDs where the first is HUM category containing "city" and second is LOC category containing "capital".'
    
    return ExperimentPayload(
        name="oolong-pairs",
        query=query,
        context=context,
        expected=pairs,
        description="TREC HUM/LOC pair extraction",
        validator=validate_id_pairs,
    )


def build_browsecomp_payload(session_id: str, doc_target: int = 1000) -> ExperimentPayload:
    """Build BrowseComp+ experiment"""
    sample = load_browsecomp_sample()
    seed = session_seed(session_id)
    
    context = build_browsecomp_context(sample, doc_target, seed)
    query = sample["query"]
    expected = sample["answer"]
    
    return ExperimentPayload(
        name="browsecomp-1k",
        query=query,
        context=context,
        expected=expected,
        description="BrowseComp+ document retrieval",
        validator=validate_needle,
    )


def build_codeqa_payload(session_id: str) -> ExperimentPayload:
    """Build CodeQA experiment"""
    entries = load_codeqa_entries()
    seed = session_seed(session_id)
    rng = random.Random(seed)
    
    entry = rng.choice(entries)
    context = build_codeqa_context(entry)
    
    query = f"{entry['question']}\n\nChoices:\n"
    query += f"A. {entry['choice_A']}\n"
    query += f"B. {entry['choice_B']}\n"
    query += f"C. {entry['choice_C']}\n"
    query += f"D. {entry['choice_D']}\n"
    query += "\nAnswer with the letter of the correct choice."
    
    return ExperimentPayload(
        name="codeqa",
        query=query,
        context=context,
        expected=entry["answer"],
        description="LongBench CodeQA reasoning",
        validator=validate_multiple_choice,
    )


# Experiment registry
EXPERIMENT_BUILDERS: Dict[str, Callable[[str], ExperimentPayload]] = {
    "oolong": lambda sid: build_oolong_payload(),
    "oolong-pairs": lambda sid: build_oolong_pairs_payload(),
    "browsecomp-1k": lambda sid: build_browsecomp_payload(sid, doc_target=1000),
    "codeqa": lambda sid: build_codeqa_payload(sid),
}


# ============================================================================
# Execution
# ============================================================================

def execute_benchmark(
    experiment_name: str,
    model_name: str,
    sub_model_name: str,
    session_id: str,
) -> Dict[str, Any]:
    """Execute a benchmark experiment"""
    start_time = time.time()
    
    try:
        # Build payload
        builder = EXPERIMENT_BUILDERS.get(experiment_name)
        if not builder:
            raise ValueError(f"Unknown experiment: {experiment_name}")
        
        payload = builder(session_id)
        stats = context_stats(payload.context)
        
        # Run RLM agent
        agent = RLMAgent(model_name=model_name, sub_model_name=sub_model_name)
        output = agent(payload.query, payload.context)
        
        # Validate (returns tuple: (passed, reason))
        validation_result = payload.validator(output, payload)
        if isinstance(validation_result, tuple):
            passed, reason = validation_result
        else:
            # Backward compatibility
            passed = validation_result
            reason = "Validation passed" if passed else "Validation failed"
        
        return {
            "experiment": experiment_name,
            "session_id": session_id,
            "model": model_name,
            "sub_model": sub_model_name,
            "passed": passed,
            "validation_reason": reason,
            "output": output,
            "expected": str(payload.expected),
            "context_stats": stats,
            "elapsed_seconds": round(time.time() - start_time, 2),
        }
    
    except Exception as exc:
        return {
            "experiment": experiment_name,
            "session_id": session_id,
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.time() - start_time, 2),
        }


def save_result_to_s3(result: dict, session_id: str):
    """Save result to S3"""
    try:
        timestamp = int(time.time())
        key = f"results/{result['experiment']}/{session_id}/{timestamp}.json"
        
        import json
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(result, indent=2),
            ContentType="application/json",
        )
        result["s3_key"] = key
    except Exception as exc:
        result["s3_error"] = f"Failed to save to S3: {exc}"


@app.entrypoint
def benchmark_handler(payload, context=None):
    """Handle benchmark invocations"""
    experiment = payload.get("experiment")
    if not experiment:
        return {"error": "Missing 'experiment' field"}
    
    if experiment not in EXPERIMENT_BUILDERS:
        return {"error": f"Unknown experiment: {experiment}"}
    
    # Check status of async task
    if payload.get("check_status"):
        session_id = payload.get("session_id", "default")
        task_id = payload.get("task_id")
        
        print(f"[Handler] Status check for session_id: {session_id}")
        print(f"[Handler] Available sessions: {list(benchmark_results.keys())}")
        
        if session_id in benchmark_results:
            print(f"[Handler] Found result for {session_id}")
            return benchmark_results[session_id]
        
        print(f"[Handler] Session {session_id} not found")
        return {"status": "not_found", "session_id": session_id}
    
    # Start new async task
    session_id = payload.get("session_id", f"session-{int(time.time())}")
    task_id = hash(f"{experiment}-{session_id}-{time.time()}") % (2**63)
    
    print(f"[Handler] Starting experiment {experiment} with session_id: {session_id}")
    
    model_name = payload.get("model_name", "amazon.nova-pro-v1:0")
    sub_model_name = payload.get("sub_model_name", "amazon.nova-micro-v1:0")
    
    def run_benchmark():
        result = execute_benchmark(experiment, model_name, sub_model_name, session_id)
        save_result_to_s3(result, session_id)
        benchmark_results[session_id] = {"status": "completed", **result}
    
    benchmark_results[session_id] = {"status": "running", "task_id": task_id}
    threading.Thread(target=run_benchmark, daemon=True).start()
    
    return {
        "status": "started",
        "task_id": task_id,
        "session_id": session_id,
        "experiment": experiment,
        "message": "Benchmark started. Poll with the same session_id and check_status=true",
    }
