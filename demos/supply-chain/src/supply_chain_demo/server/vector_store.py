"""Pure-Python TF-IDF vector similarity search over maritime disruption bulletins."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from supply_chain_demo.server.corpus import MARITIME_BULLETINS, BulletinRecord

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric terms, splitting snake_case corridors."""
    normalized = text.lower().replace("_", " ").replace("-", " ")
    tokens = _TOKEN_RE.findall(normalized)
    raw_snake = re.findall(r"[a-z0-9_]+", text.lower())
    # Keep exact snake_case corridor identifiers alongside split words for strong matching.
    return tokens + [tok for tok in raw_snake if "_" in tok]


class MaritimeBulletinIndex:
    """In-memory TF-IDF cosine-similarity vector index over maritime disruption bulletins."""

    def __init__(self, bulletins: list[BulletinRecord] | None = None) -> None:
        self._bulletins = bulletins if bulletins is not None else list(MARITIME_BULLETINS)
        self._idf: dict[str, float] = {}
        self._doc_vectors: list[dict[str, float]] = []
        self._doc_norms: list[float] = []
        self._build_index()

    def _build_index(self) -> None:
        n_docs = len(self._bulletins)
        doc_freqs: Counter[str] = Counter()
        term_counts_list: list[Counter[str]] = []

        for bulletin in self._bulletins:
            # Weight the region/summary slightly by repeating metadata text once in indexable doc.
            index_text = f"{bulletin.region} {bulletin.summary} {bulletin.text}"
            counts = Counter(_tokenize(index_text))
            term_counts_list.append(counts)
            for term in counts:
                doc_freqs[term] += 1

        self._idf = {
            term: math.log((1.0 + n_docs) / (1.0 + df)) + 1.0
            for term, df in doc_freqs.items()
        }

        self._doc_vectors = []
        self._doc_norms = []
        for counts in term_counts_list:
            total = sum(counts.values()) or 1
            vec = {
                term: (count / total) * self._idf[term]
                for term, count in counts.items()
            }
            norm = math.sqrt(sum(val * val for val in vec.values())) or 1.0
            self._doc_vectors.append(vec)
            self._doc_norms.append(norm)

    def _embed_query(self, query: str) -> tuple[dict[str, float], float]:
        counts = Counter(_tokenize(query))
        total = sum(counts.values()) or 1
        vec = {
            term: (count / total) * self._idf.get(term, 1.0)
            for term, count in counts.items()
            if term in self._idf
        }
        norm = math.sqrt(sum(val * val for val in vec.values())) or 1.0
        return vec, norm

    def search(self, region: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return the top-k most relevant maritime bulletins for a region query."""
        q_vec, q_norm = self._embed_query(region)
        scored: list[tuple[float, BulletinRecord]] = []

        for bulletin, doc_vec, doc_norm in zip(
            self._bulletins, self._doc_vectors, self._doc_norms, strict=True
        ):
            dot = sum(weight * doc_vec.get(term, 0.0) for term, weight in q_vec.items())
            cosine = dot / (q_norm * doc_norm) if q_vec else 0.0
            if bulletin.region == region:
                cosine += 0.35
            scored.append((cosine, bulletin))

        scored.sort(key=lambda item: (item[0], item[1].published_at), reverse=True)
        top_results = scored[: max(1, top_k)]
        return [
            {
                "bulletin_id": item.bulletin_id,
                "region": item.region,
                "published_at": item.published_at,
                "alert_severity": item.alert_severity,
                "estimated_delay_days": item.estimated_delay_days,
                "similarity_score": round(score, 4),
                "summary": item.summary,
                "raw_chunk_text": item.text,
            }
            for score, item in top_results
        ]
