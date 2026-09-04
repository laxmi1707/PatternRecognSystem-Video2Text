from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_search_returns_empty_list_with_no_corpus_configured(monkeypatch):
    from app.services.search_service import search_service

    monkeypatch.setattr(search_service, "_index", None)
    monkeypatch.setattr("app.config.settings.search_corpus_dir", None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/search", json={"query": "open a new file"})

    assert resp.status_code == 200
    assert resp.json() == {"results": []}
