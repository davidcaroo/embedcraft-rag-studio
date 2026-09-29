"""Unit tests for MemoryVectorStore and LanceDBVectorStore."""

from pathlib import Path

from embedcraft.adapters.vector_stores.lancedb_store import LanceDBVectorStore
from embedcraft.adapters.vector_stores.memory_store import MemoryVectorStore
from embedcraft.ports.vector_store import VectorRecord


def test_memory_vector_store():
    store = MemoryVectorStore()
    col_id = "col-123"
    rev_id = "rev-456"

    store.create_collection_index(col_id, rev_id, dimension=3)

    records = [
        VectorRecord(
            chunk_id="chunk-1",
            document_id="doc-1",
            vector=[1.0, 0.0, 0.0],
            text="First chunk about apples",
            metadata={"source": "fruit.txt"},
        ),
        VectorRecord(
            chunk_id="chunk-2",
            document_id="doc-1",
            vector=[0.0, 1.0, 0.0],
            text="Second chunk about oranges",
            metadata={"source": "fruit.txt"},
        ),
    ]

    store.upsert(col_id, rev_id, records)

    # Query with vector closer to [1.0, 0.1, 0.0]
    results = store.search(col_id, rev_id, query_vector=[0.9, 0.1, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "chunk-1"
    assert results[0].score > 0.9
    assert results[0].metadata["source"] == "fruit.txt"

    # Test delete
    deleted = store.delete_revision(col_id, rev_id)
    assert deleted is True
    assert store.search(col_id, rev_id, query_vector=[1.0, 0.0, 0.0]) == []


def test_lancedb_vector_store(temp_dir: Path):
    db_dir = temp_dir / "lancedb_test"
    store = LanceDBVectorStore(base_dir=db_dir)

    col_id = "col-abc-123"
    rev_id = "rev-xyz-456"

    store.create_collection_index(col_id, rev_id, dimension=4)

    records = [
        VectorRecord(
            chunk_id="c1",
            document_id="d1",
            vector=[1.0, 0.0, 0.0, 0.0],
            text="Alpha vector text",
            metadata={"page": 1},
        ),
        VectorRecord(
            chunk_id="c2",
            document_id="d2",
            vector=[0.0, 0.0, 1.0, 0.0],
            text="Gamma vector text",
            metadata={"page": 2},
        ),
    ]

    store.upsert(col_id, rev_id, records)

    # Search
    results = store.search(col_id, rev_id, query_vector=[0.95, 0.05, 0.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[0].score > 0.8
    assert results[0].metadata["page"] == 1

    # Delete
    del_ok = store.delete_revision(col_id, rev_id)
    assert del_ok is True
    assert store.search(col_id, rev_id, query_vector=[1.0, 0.0, 0.0, 0.0]) == []
