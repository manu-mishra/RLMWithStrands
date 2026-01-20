"""Context builders for different experiment types"""
import random
from typing import List, Dict, Any

# Filler text for synthetic haystacks
FILLER_SENTENCES = [
    "Market analysts project sustained growth throughout the next fiscal year. ",
    "The quarterly earnings report exceeded investor expectations by a significant margin. ",
    "Strategic partnerships are being formed to expand into emerging markets. ",
    "Operational efficiency improvements have reduced costs by fifteen percent. ",
    "Customer satisfaction scores reached an all-time high this quarter. ",
]


def build_haystack_context(total_chars: int, needle: str, seed: int) -> List[str]:
    """Build synthetic haystack with embedded needle"""
    rng = random.Random(seed)
    chunk_target = max(200_000, total_chars // 16)
    
    # Generate haystack chunks
    chunks: List[str] = []
    remaining = total_chars
    needle_inserted = False
    
    while remaining > 0:
        target = min(chunk_target, remaining)
        buffer: List[str] = []
        current = 0
        
        while current < target:
            sentence = rng.choice(FILLER_SENTENCES)
            buffer.append(sentence)
            current += len(sentence)
        
        chunk = "".join(buffer)[:target]
        
        # Insert needle in middle chunk
        if not needle_inserted and len(chunks) >= 8:
            chunk = chunk[:len(chunk)//2] + needle + chunk[len(chunk)//2:]
            needle_inserted = True
        
        chunks.append(chunk)
        remaining -= target
    
    return chunks


def build_trec_context(entries: List[Dict[str, str]], block_size: int = 200) -> List[str]:
    """Build context from TREC entries in blocks"""
    chunks: List[str] = []
    for i in range(0, len(entries), block_size):
        block = entries[i:i + block_size]
        lines = [f"{e['id']}: {e['text']} (Label: {e['label']})" for e in block]
        chunks.append("\n".join(lines))
    return chunks


def build_browsecomp_context(sample: Dict[str, Any], doc_target: int, seed: int) -> List[str]:
    """Build context from BrowseComp+ documents"""
    rng = random.Random(seed)
    
    # Combine gold and negative docs
    all_docs = sample.get("gold_docs", []) + sample.get("negative_docs", [])
    rng.shuffle(all_docs)
    
    chunks: List[str] = []
    for doc in all_docs[:doc_target]:
        chunks.append(f"Document ID: {doc['docid']}\n{doc['text']}")
    
    return chunks


def build_codeqa_context(entry: Dict[str, Any]) -> List[str]:
    """Build context from CodeQA repository files"""
    return [entry["context"]]
