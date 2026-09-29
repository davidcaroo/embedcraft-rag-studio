"""Unit tests for ChatService, MockLLMProvider, and LexicalScoringReranker."""

import json
from unittest.mock import MagicMock

from embedcraft.adapters.llm.mock_provider import MockLLMProvider
from embedcraft.adapters.rerankers.scoring_reranker import LexicalScoringReranker
from embedcraft.application.services.chat_service import ChatService
from embedcraft.domain.entities import Citation, RetrievalResult
from embedcraft.domain.value_objects import SearchMode


def test_mock_llm_provider_grounding():
    provider = MockLLMProvider()

    # 1. Empty context triggers insufficient evidence
    resp_empty = provider.generate("CONTEXTO PROPORCIONADO:\n\n\n\nPREGUNTA:\nCual es la velocidad?")
    assert "No cuento con evidencia suficiente" in resp_empty.content

    # 2. Context with content generates grounded response with citation
    resp_grounded = provider.generate(
        "CONTEXTO PROPORCIONADO:\n[1] Archivo: doc.txt\nLa velocidad máxima del rover es de 15 km/h.\n\nPREGUNTA:\nCual es la velocidad?\nRESPUESTA FUNDAMENTADA:"
    )
    assert "15 km/h" in resp_grounded.content
    assert "[1]" in resp_grounded.content
    assert resp_grounded.prompt_tokens > 0
    assert resp_grounded.completion_tokens > 0


def test_lexical_scoring_reranker():
    reranker = LexicalScoringReranker()
    query = "arquitectura hexagonal puertos adaptadores"

    r1 = RetrievalResult(
        chunk_id="c1",
        text="La arquitectura hexagonal separa el dominio mediante puertos y adaptadores desacoplados.",
        score=0.7,
        citation=Citation(document_path="arch.md", chunk_id="c1"),
    )
    r2 = RetrievalResult(
        chunk_id="c2",
        text="El motor de base de datos utiliza tablas SQLite con soporte WAL.",
        score=0.8,
        citation=Citation(document_path="db.md", chunk_id="c2"),
    )

    reranked = reranker.rerank(query=query, results=[r2, r1], top_k=2)
    assert len(reranked) == 2
    # r1 has much higher term overlap with query, so it should rank first
    assert reranked[0].chunk_id == "c1"
    assert "rerank_score" in reranked[0].metadata


def test_chat_service_workflow_and_diagnostics():
    mock_indexing = MagicMock()
    mock_indexing.search.return_value = [
        RetrievalResult(
            chunk_id="chunk-42",
            text="EmbedCraft RAG Studio almacena vectores en LanceDB localmente.",
            score=0.92,
            citation=Citation(
                document_path="manual.pdf",
                document_title="Manual",
                chunk_id="chunk-42",
                page=3,
                section="Almacenamiento",
                snippet="EmbedCraft RAG Studio almacena vectores en LanceDB localmente.",
            ),
        )
    ]

    llm = MockLLMProvider()
    reranker = LexicalScoringReranker()
    chat_svc = ChatService(indexing_service=mock_indexing, llm_provider=llm, reranker=reranker)

    # 1. Ask query with rerank
    diag = chat_svc.ask(
        project_identifier="test-proj",
        query="Donde almacena vectores EmbedCraft?",
        mode=SearchMode.HYBRID,
        top_k=1,
        use_reranker=True,
    )

    assert "LanceDB" in diag.answer
    assert "[1]" in diag.answer
    assert len(diag.citations) == 1
    assert diag.citations[0].document_path == "manual.pdf"
    assert diag.latencies.retrieval_ms >= 0.0
    assert diag.latencies.rerank_ms >= 0.0
    assert diag.latencies.generation_ms >= 0.0
    assert diag.latencies.total_ms >= 0.0
    assert diag.tokens.total_tokens > 0

    # 2. Retrieval only mode
    diag_ro = chat_svc.ask(
        project_identifier="test-proj",
        query="Donde almacena vectores?",
        retrieval_only=True,
    )
    assert diag_ro.retrieval_only is True
    assert "[MODO SOLO RECUPERACIÓN]" in diag_ro.answer
    assert len(diag_ro.citations) == 1

    # 3. Export JSON
    json_str = chat_svc.export_session_to_json(diag)
    parsed = json.loads(json_str)
    assert parsed["project_identifier"] == "test-proj"
    assert "latencies" in parsed
    assert "citations" in parsed
