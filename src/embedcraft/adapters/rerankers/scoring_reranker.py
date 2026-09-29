"""Lightweight lexical and term-overlap reranker adapter."""

from __future__ import annotations

import re
from collections.abc import Sequence

from embedcraft.domain.entities import RetrievalResult
from embedcraft.ports.reranker import RerankerProvider


class LexicalScoringReranker(RerankerProvider):
    """Reranker that re-evaluates retrieval candidates using term overlap and query coverage."""

    def rerank(
        self,
        query: str,
        results: Sequence[RetrievalResult],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not results:
            return []

        query_tokens = set(re.findall(r"\w+", query.lower()))
        if not query_tokens:
            return list(results[:top_k])

        scored: list[tuple[float, RetrievalResult]] = []
        for r in results:
            text_tokens = re.findall(r"\w+", r.text.lower())
            total_text_tokens = max(1, len(text_tokens))

            # 1. Query Term Coverage (how many unique query words appear in chunk)
            matched_tokens = query_tokens.intersection(text_tokens)
            coverage = len(matched_tokens) / len(query_tokens)

            # 2. Term Frequency Density
            freq_count = sum(text_tokens.count(t) for t in query_tokens)
            density = min(1.0, freq_count / total_text_tokens * 5.0)

            # 3. Exact phrase match bonus
            phrase_bonus = 0.3 if query.lower().strip() in r.text.lower() else 0.0

            # Composite rerank score combining original retriever score with lexical precision
            rerank_score = (0.5 * r.score) + (0.3 * coverage) + (0.1 * density) + (0.1 * phrase_bonus)

            updated_res = r.model_copy()
            updated_res.metadata["original_score"] = r.score
            updated_res.metadata["rerank_score"] = float(rerank_score)
            updated_res.score = float(rerank_score)

            scored.append((rerank_score, updated_res))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [res for _, res in scored[:top_k]]
