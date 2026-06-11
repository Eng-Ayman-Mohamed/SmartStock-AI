"""
retrieval.py — Task O8
Hybrid search: dense vector similarity (pgvector) + PostgreSQL full-text search.
Combines both result sets, deduplicates, and returns chunks with scores.
"""

import logging
import os

from django.db import connection

from ai.rag.ingestion import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


def _get_embedding_model():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def _dense_search(query: str, query_embedding: list[float], top_k: int = 10) -> list[dict]:
    """Cosine similarity search via pgvector."""
    sql = """
        SELECT
            id,
            chunk_text,
            source_document,
            page_number,
            metadata,
            1 - (embedding <=> %s::vector) AS vector_score
        FROM ingestion_documentchunk
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """
    embedding_str = '[' + ','.join(str(v) for v in query_embedding) + ']'
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [embedding_str, embedding_str, top_k])
            rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'content': row[1],
                'source_document': row[2],
                'page_number': row[3],
                'metadata': row[4] or {},
                'score': float(row[5]) if row[5] is not None else 0.0,
                'vector_score': float(row[5]) if row[5] is not None else 0.0,
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning('Dense search failed: %s', e)
        return []


def _sparse_search(query: str, top_k: int = 10) -> list[dict]:
    """PostgreSQL full-text search using tsvector/tsquery."""
    sql = """
        SELECT
            id,
            chunk_text,
            source_document,
            page_number,
            metadata,
            ts_rank("tsvector", plainto_tsquery('english', %s)) AS fts_score
        FROM ingestion_documentchunk
        WHERE "tsvector" @@ plainto_tsquery('english', %s)
        ORDER BY fts_score DESC
        LIMIT %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [query, query, top_k])
            rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'content': row[1],
                'source_document': row[2],
                'page_number': row[3],
                'metadata': row[4] or {},
                'score': float(row[5]) if row[5] is not None else 0.0,
                'fts_score': float(row[5]) if row[5] is not None else 0.0,
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning('Sparse search failed: %s', e)
        return []


def hybrid_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Combine dense (vector) and sparse (FTS) search results.
    Deduplicates by chunk ID. Chunks appearing in both sets
    get a combined score = max(vector_score, fts_score).
    """
    embeddings = _get_embedding_model()
    query_embedding = embeddings.embed_query(query)

    dense_results = _dense_search(query, query_embedding, top_k=top_k)
    sparse_results = _sparse_search(query, top_k=top_k)

    # Merge by chunk ID, keeping the best score from each source
    merged: dict[int, dict] = {}
    for chunk in dense_results:
        cid = chunk['id']
        merged[cid] = chunk

    for chunk in sparse_results:
        cid = chunk['id']
        if cid in merged:
            existing = merged[cid]
            existing['fts_score'] = chunk.get('fts_score', 0)
            vector_score = existing.get('vector_score', 0)
            fts_score = existing.get('fts_score', 0)
            normalized_fts = min(fts_score, 1.0)
            combined = (vector_score + normalized_fts) / 2
            existing['score'] = combined
        else:
            merged[cid] = chunk

    results = sorted(merged.values(), key=lambda c: c.get('score', 0), reverse=True)
    return results[:top_k]
