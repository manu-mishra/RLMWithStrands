"""Dataset loading utilities for benchmarks"""
import json
from pathlib import Path
from typing import Dict, List, Any
import boto3
import os

s3_client = boto3.client("s3")
S3_BUCKET = os.environ.get("S3_RESULTS_BUCKET", "rlm-benchmark-results-local")
DATASET_PREFIX = os.environ.get("DATASET_PREFIX", "datasets")
LOCAL_DATASET_DIR = Path(os.environ.get("DATASET_CACHE_DIR", "/tmp/rlm_datasets"))
LOCAL_DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Caches
_trec_cache: List[Dict[str, str]] | None = None
_codeqa_cache: List[Dict[str, Any]] | None = None
_browsecomp_cache: Dict[str, Any] | None = None


def get_dataset_path(relative_key: str) -> Path:
    """Get local path to dataset, downloading from S3 if needed"""
    normalized = relative_key.replace("\\", "/").lstrip("/")
    local_path = LOCAL_DATASET_DIR / normalized
    
    if local_path.exists():
        return local_path
    
    if not S3_BUCKET:
        raise RuntimeError(f"S3_RESULTS_BUCKET is not configured. Current value: {S3_BUCKET}")
    
    local_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = DATASET_PREFIX.strip("/")
    s3_key = "/".join(filter(None, [prefix, normalized]))
    
    try:
        s3_client.download_file(S3_BUCKET, s3_key, str(local_path))
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download dataset asset {normalized} from s3://{S3_BUCKET}/{s3_key}. "
            f"Error: {type(exc).__name__}: {exc}"
        ) from exc
    
    return local_path


def load_trec_entries() -> List[Dict[str, str]]:
    """Load TREC dataset with caching"""
    global _trec_cache
    if _trec_cache is not None:
        return _trec_cache
    
    dataset_path = get_dataset_path("trec/train_5500.label")
    entries: List[Dict[str, str]] = []
    
    with dataset_path.open("r", encoding="latin-1") as infile:
        for idx, line in enumerate(infile):
            if not line.strip():
                continue
            label, question = line.strip().split(" ", 1)
            coarse = label.split(":")[0]
            entries.append({"id": f"Q{idx:04d}", "label": coarse, "text": question})
    
    _trec_cache = entries
    return entries


def load_codeqa_entries() -> List[Dict[str, Any]]:
    """Load CodeQA dataset with caching"""
    global _codeqa_cache
    if _codeqa_cache is not None:
        return _codeqa_cache
    
    dataset_path = get_dataset_path("longbench_codeqa.json")
    with dataset_path.open("r", encoding="utf-8") as infile:
        _codeqa_cache = json.load(infile)
    
    return _codeqa_cache


def load_browsecomp_sample() -> Dict[str, Any]:
    """Load BrowseComp+ dataset with caching"""
    global _browsecomp_cache
    if _browsecomp_cache is not None:
        return _browsecomp_cache
    
    dataset_path = get_dataset_path("browsecomp_plus_sample.json")
    with dataset_path.open("r", encoding="utf-8") as infile:
        data = json.load(infile)
        # Return first sample if data is a list
        _browsecomp_cache = data[0] if isinstance(data, list) else data
    
    return _browsecomp_cache
