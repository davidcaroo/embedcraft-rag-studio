"""Unit tests for EvaluationService metrics calculation (Recall@K, Hit Rate, MRR, Citation Coverage)."""

import json
from unittest.mock import MagicMock

import pytest

from embedcraft.application.services.evaluation_service import EvaluationService
from embedcraft.domain.entities import (
    Citation,
    EvaluationItem,
    EvaluationReport,
    RetrievalResult,
)


def _make_result(doc_path: str, chunk_id: str, text: str = "some text") -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        text=text,
        score=0.9,
        citation=Citation(
            document_path=doc_path,
            chunk_id=chunk_id,
            snippet=text,
        ),
    )


def test_evaluation_service_metrics_calculation(tmp_path):
    # Mock indexing service search
    indexing_svc = MagicMock()

    # Query 1: expected 'legal/doc1.pdf' -> returned at rank 1 (index 0)
    # Query 2: expected 'finance/q4.pdf' -> returned at rank 2 (index 1)
    # Query 3: expected 'tech/arch.md' -> not returned (miss)
    def fake_search(*args, query: str = "", **kwargs):
        if "legal" in query:
            return [
                _make_result("legal/doc1.pdf", "c1"),
                _make_result("other/doc.pdf", "c2"),
            ]
        elif "finance" in query:
            return [
                _make_result("other/doc.pdf", "c3"),
                _make_result("finance/q4.pdf", "c4"),
            ]
        else:
            return [
                _make_result("random/doc.pdf", "c5"),
                _make_result("other/doc.pdf", "c6"),
            ]

    indexing_svc.search.side_effect = fake_search

    eval_service = EvaluationService(indexing_service=indexing_svc)

    items = [
        EvaluationItem(
            query="consultar estatuto legal",
            expected_documents=["legal/doc1.pdf"],
        ),
        EvaluationItem(
            query="revisar balance finance",
            expected_documents=["finance/q4.pdf"],
        ),
        EvaluationItem(
            query="arquitectura de red",
            expected_documents=["tech/arch.md"],
        ),
    ]

    report = eval_service.evaluate_dataset("corp-proj", items, top_k=5)

    assert isinstance(report, EvaluationReport)
    assert report.total_queries == 3
    # 2 hits out of 3 queries -> Hit rate = 2/3 = 0.6667
    assert pytest.approx(report.hit_rate, 0.01) == 0.67
    # Reciprocal ranks: 1.0 (rank 1), 0.5 (rank 2), 0.0 (miss) -> MRR = 1.5 / 3 = 0.50
    assert pytest.approx(report.mrr, 0.01) == 0.50
    # Recall@K: 2 found / 3 queries = 0.67
    assert pytest.approx(report.recall_at_k, 0.01) == 0.67
    # All returned results had citations -> Citation coverage = 1.0
    assert pytest.approx(report.citation_coverage, 0.01) == 1.0
    assert len(report.results) == 3


def test_evaluation_service_from_json_file(tmp_path):
    indexing_svc = MagicMock()
    indexing_svc.search.return_value = [_make_result("policy.pdf", "c10")]

    eval_service = EvaluationService(indexing_service=indexing_svc)

    dataset_path = tmp_path / "dataset.json"
    dataset_data = [
        {
            "query": "¿Cuál es la política de seguridad?",
            "expected_documents": ["policy.pdf"],
            "expected_chunks": ["c10"],
        }
    ]
    dataset_path.write_text(json.dumps(dataset_data), encoding="utf-8")

    report = eval_service.evaluate_from_file("security-proj", dataset_path, top_k=3)
    assert report.total_queries == 1
    assert report.hit_rate == 1.0
    assert report.mrr == 1.0
