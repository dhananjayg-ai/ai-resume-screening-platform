"""Duplicate resume detection via Jaccard similarity over shingled (k-gram)
tokens of resume text.
"""
import re


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", (text or "").lower())


def _shingles(tokens: list[str], k: int) -> set[tuple[str, ...]]:
    if len(tokens) < k:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard_similarity(text_a: str, text_b: str, k: int = 5) -> float:
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    shingles_a = _shingles(tokens_a, k)
    shingles_b = _shingles(tokens_b, k)
    if not shingles_a and not shingles_b:
        return 1.0
    if not shingles_a or not shingles_b:
        return 0.0
    intersection = shingles_a & shingles_b
    union = shingles_a | shingles_b
    return len(intersection) / len(union) if union else 0.0


def find_most_similar_candidate(
    new_text: str,
    existing: list[tuple[int, str]],
    k: int = 5,
    threshold: float = 0.6,
) -> tuple[int | None, float]:
    """existing: list of (candidate_id, raw_text) tuples to compare against.

    Returns (best_matching_candidate_id_or_None, best_similarity).
    Only returns a candidate id if similarity >= threshold.
    """
    best_id = None
    best_score = 0.0
    for candidate_id, text in existing:
        score = jaccard_similarity(new_text, text, k=k)
        if score > best_score:
            best_score = score
            best_id = candidate_id
    if best_score >= threshold:
        return best_id, best_score
    return None, best_score
