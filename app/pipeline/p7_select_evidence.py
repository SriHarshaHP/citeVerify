import re
from typing import List
from rank_bm25 import BM25Okapi
from app.schemas import TextChunk
from app.pipeline.number_checker import extract_numbers_from_text

def tokenize(text: str) -> List[str]:
    """Basic lowercased word tokenization."""
    return re.findall(r'\b\w+\b', text.lower())

def select_top_evidence_chunks(
    claim_text: str,
    chunks: List[TextChunk],
    top_k: int = 4
) -> List[TextChunk]:
    """
    Ranks text chunks using BM25 and boosts chunks containing claim numbers.
    Returns the top k most relevant TextChunk objects.
    """
    if not chunks:
        return []
    if len(chunks) <= top_k:
        return chunks

    corpus = [tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(corpus)

    query_tokens = tokenize(claim_text)
    scores = bm25.get_scores(query_tokens)

    # Number boost
    claim_nums = extract_numbers_from_text(claim_text)
    claim_num_vals = [n["value"] for n in claim_nums]

    ranked_indices = []
    for idx, chunk in enumerate(chunks):
        score = scores[idx]
        # Check if chunk contains any claim number
        chunk_nums = extract_numbers_from_text(chunk.text)
        chunk_vals = [n["value"] for n in chunk_nums]
        if any(cv in chunk_vals for cv in claim_num_vals):
            score += 3.0  # Significant boost for number co-occurrence
        ranked_indices.append((score, idx))

    ranked_indices.sort(key=lambda x: x[0], reverse=True)
    selected = [chunks[idx] for _, idx in ranked_indices[:top_k]]
    return selected
