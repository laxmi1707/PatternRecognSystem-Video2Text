"""A retrieval-only prototype -- the "R" in RAG.

Indexes the per-task "workflow" descriptions already sitting in each app
folder's video2knowledge_labels.jsonl and answers a query with the
closest-matching real snippets, ranked by TF-IDF cosine similarity.

Two things this deliberately does NOT do, both by necessity rather than choice:

1. It stands in for the real corpus. The project's Search feature is meant to
   search *this system's own generated SOPs*, once enough videos have been
   analyzed to search over. There aren't enough yet, so this indexes the
   VideoCUA task descriptions instead, purely to prove the retrieval
   mechanism end to end.
2. It has no generation step. Turning ranked snippets into a synthesized
   answer needs an LLM (the architecture doc names AWS Bedrock), and no LLM
   credentials are configured in this repo. This returns ranked real
   snippets -- a search result list, not a chatbot answer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchDocument:
    task_id: int
    app: str
    workflow: str


@dataclass
class SearchResult:
    task_id: int
    app: str
    snippet: str
    score: float


def load_documents(data_dir: str | Path) -> list[SearchDocument]:
    """One document per task_id, deduped (each jsonl repeats it once per action row)."""
    root = Path(data_dir)
    seen: dict[int, SearchDocument] = {}
    for app_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        jsonl_path = app_dir / "video2knowledge_labels.jsonl"
        if not jsonl_path.exists():
            continue
        for line in jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            task_id = row.get("task_id")
            workflow = (row.get("workflow") or row.get("nl") or "").strip()
            if task_id is None or not workflow or workflow.lower() == "not required":
                continue
            seen.setdefault(task_id, SearchDocument(task_id=task_id, app=row.get("app", app_dir.name), workflow=workflow))
    return list(seen.values())


class SearchIndex:
    """scikit-learn (the `ml` extra) is only imported here, lazily, and only
    when there's a non-empty corpus to index. Everyone without the extra --
    or without a configured corpus -- can still import and boot the app;
    they just get an index that always returns no results."""

    def __init__(self, documents: list[SearchDocument]) -> None:
        self._documents = documents
        self._vectorizer = None
        self._matrix = None
        if documents:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
            self._matrix = self._vectorizer.fit_transform([d.workflow for d in documents])

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if self._matrix is None:
            return []
        from sklearn.metrics.pairwise import cosine_similarity

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            SearchResult(task_id=self._documents[i].task_id, app=self._documents[i].app,
                         snippet=self._documents[i].workflow, score=float(scores[i]))
            for i in ranked if scores[i] > 0
        ]
