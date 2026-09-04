"""Wraps the retrieval prototype (app/ml/retrieval.py) as a lazily-built,
request-time search service. The index is built once, on first search --
see app/ml/retrieval.py's module docstring for what this does and doesn't do.

No corpus is checked into the repo, so search_corpus_dir is unset by default
and every developer's machine is expected to have a different (or no) local
copy -- search() degrades to an empty result list rather than erroring out
when there's nothing to index.
"""
from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.ml.retrieval import SearchIndex, SearchResult, load_documents


class SearchService:
    def __init__(self) -> None:
        self._index: SearchIndex | None = None

    def _ensure_index(self) -> SearchIndex:
        if self._index is None:
            corpus_dir = settings.search_corpus_dir
            documents = load_documents(corpus_dir) if corpus_dir and Path(corpus_dir).is_dir() else []
            self._index = SearchIndex(documents)
        return self._index

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        return self._ensure_index().search(query, top_k=top_k)


search_service = SearchService()
