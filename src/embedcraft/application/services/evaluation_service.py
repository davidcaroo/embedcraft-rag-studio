"""RAG evaluation service computing Recall@K, Hit Rate, MRR, Precision@K, and Citation Coverage."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from embedcraft.domain.entities import (
    EvaluationItem,
    EvaluationReport,
    QueryEvaluationResult,
    utc_now,
)
from embedcraft.domain.exceptions import EmbedCraftError
from embedcraft.domain.value_objects import SearchMode


class EvaluationService:
    """Computes technical information-retrieval and grounding metrics against benchmark datasets."""

    def __init__(self, indexing_service: Any) -> None:
        self.indexing_service = indexing_service

    def evaluate_from_file(
        self,
        project_name: str,
        file_path: Path | str,
        top_k: int = 10,
        mode: SearchMode = SearchMode.HYBRID,
    ) -> EvaluationReport:
        """Loads benchmark queries from a JSON or YAML file and executes evaluation."""
        path = Path(file_path)
        if not path.exists():
            raise EmbedCraftError(f"Evaluation dataset file not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception as exc:
            raise EmbedCraftError(f"Failed to parse evaluation dataset JSON: {exc}") from exc

        if not isinstance(data, list):
            raise EmbedCraftError("Evaluation dataset must be a JSON array of query objects.")

        items: list[EvaluationItem] = []
        for raw in data:
            items.append(
                EvaluationItem(
                    query=raw.get("query", ""),
                    expected_documents=raw.get("expected_documents", []),
                    expected_chunks=raw.get("expected_chunks", []),
                    reference_answer=raw.get("reference_answer", ""),
                )
            )

        return self.evaluate_dataset(project_name=project_name, items=items, top_k=top_k, mode=mode)

    def evaluate_dataset(
        self,
        project_name: str,
        items: list[EvaluationItem],
        top_k: int = 10,
        mode: SearchMode = SearchMode.HYBRID,
    ) -> EvaluationReport:
        """Executes retrieval queries against project index and calculates IR benchmark metrics."""
        if not items:
            return EvaluationReport(
                project_name=project_name,
                total_queries=0,
                k=top_k,
                hit_rate=0.0,
                mrr=0.0,
                recall_at_k=0.0,
                precision_at_k=0.0,
                citation_coverage=0.0,
                avg_latency_ms=0.0,
                results=[],
                evaluated_at=utc_now(),
            )

        query_results: list[QueryEvaluationResult] = []
        reciprocal_ranks: list[float] = []
        hits: list[bool] = []
        citation_counts: list[float] = []
        latencies: list[float] = []
        total_relevant_retrieved = 0

        for item in items:
            start_time = time.perf_counter()
            results = self.indexing_service.search(
                project_identifier=project_name,
                query=item.query,
                mode=mode,
                top_k=top_k,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            latencies.append(elapsed_ms)

            first_rank: int | None = None
            relevant_in_query = 0
            valid_citations = 0

            # Match criteria: check document path or chunk id
            expected_docs_norm = [
                d.replace("\\", "/").lower().strip() for d in item.expected_documents
            ]
            expected_chunks_set = set(item.expected_chunks)

            top_sources: list[str] = []
            for rank, r in enumerate(results, start=1):
                doc_path = r.citation.document_path.replace("\\", "/").lower()
                top_sources.append(r.citation.document_path)

                if r.citation.document_path.strip():
                    valid_citations += 1

                is_match = False
                if r.chunk_id in expected_chunks_set:
                    is_match = True
                elif any(
                    exp in doc_path or doc_path.endswith(exp) or Path(doc_path).name == Path(exp).name
                    for exp in expected_docs_norm
                ):
                    is_match = True

                if is_match:
                    relevant_in_query += 1
                    if first_rank is None:
                        first_rank = rank

            has_hit = first_rank is not None
            rr = (1.0 / first_rank) if has_hit and first_rank else 0.0

            hits.append(has_hit)
            reciprocal_ranks.append(rr)
            total_relevant_retrieved += relevant_in_query

            coverage = (valid_citations / len(results)) if results else 1.0
            citation_counts.append(coverage)

            query_results.append(
                QueryEvaluationResult(
                    query=item.query,
                    hit=has_hit,
                    reciprocal_rank=rr,
                    retrieved_count=len(results),
                    relevant_retrieved=relevant_in_query,
                    latency_ms=elapsed_ms,
                    top_sources=top_sources,
                )
            )

        n = len(items)
        hit_rate = sum(1 for h in hits if h) / n
        mrr = sum(reciprocal_ranks) / n
        recall_at_k = hit_rate  # proportion of queries with ground truth found in top k
        precision_at_k = total_relevant_retrieved / (n * top_k) if (n * top_k) > 0 else 0.0
        citation_coverage = sum(citation_counts) / n if n > 0 else 0.0
        avg_latency = sum(latencies) / n if n > 0 else 0.0

        return EvaluationReport(
            project_name=project_name,
            total_queries=n,
            k=top_k,
            hit_rate=hit_rate,
            mrr=mrr,
            recall_at_k=recall_at_k,
            precision_at_k=precision_at_k,
            citation_coverage=citation_coverage,
            avg_latency_ms=avg_latency,
            results=query_results,
            evaluated_at=utc_now(),
        )
