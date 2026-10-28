"""The analysis job must not block the event loop.

Feature extraction and classification are slow, synchronous CPU work. If they run on the
event loop, /health and job-status requests stall for the whole analysis and the load
balancer can mark the task unhealthy. These tests stand in a blocking time.sleep for that
work and check that other coroutines keep running meanwhile.
"""
from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace

import numpy as np
import pytest

from app.services import classification_service as cs

BLOCK_S = 0.5
TICK_S = 0.05


async def _count_ticks_while(coro) -> tuple[int, object]:
    """Run coro and count how often a concurrent ticker coroutine gets scheduled."""
    ticks = 0
    done = asyncio.Event()

    async def ticker():
        nonlocal ticks
        while not done.is_set():
            ticks += 1
            await asyncio.sleep(TICK_S)

    task = asyncio.create_task(ticker())
    try:
        result = await coro
    finally:
        done.set()
        await task
    return ticks, result


@pytest.fixture
def no_db(monkeypatch):
    async def update_job_status(*args, **kwargs):
        return None

    monkeypatch.setattr(cs, "update_job_status", update_job_status)
    return SimpleNamespace(add_all=lambda results: None)


@pytest.mark.asyncio
async def test_feature_extraction_runs_off_the_event_loop(monkeypatch, no_db):
    def slow_extract(video_path, action_log_path, on_progress=None):
        time.sleep(BLOCK_S)
        return np.zeros((2, 4)), [{"start_time": 0.0, "end_time": 1.0}] * 2, False

    async def no_models(X, db=None, job_id=None):
        return {}

    monkeypatch.setattr(cs, "_extract_features", slow_extract)
    monkeypatch.setattr(cs, "_classify_all_models", no_models)

    job = SimpleNamespace(id=1)
    ticks, _ = await _count_ticks_while(cs.run_classification_job(no_db, job))

    # A blocked loop would let the ticker run once; a free one runs it every TICK_S.
    assert ticks >= (BLOCK_S / TICK_S) // 2


@pytest.mark.asyncio
async def test_classification_runs_off_the_event_loop(monkeypatch):
    def slow_classify(X, model_name):
        time.sleep(BLOCK_S / 2)
        return {"results": [{"label": "other", "model_name": model_name}]}

    monkeypatch.setattr(cs, "_classify_locked", slow_classify)
    monkeypatch.setattr(cs, "_get_available_models", lambda: ["svm", "mlp"])

    ticks, results = await _count_ticks_while(cs._classify_all_models(np.zeros((1, 4))))

    assert set(results) == {"svm", "mlp"}
    assert ticks >= (BLOCK_S / TICK_S) // 2


@pytest.mark.asyncio
async def test_failed_model_is_skipped_not_raised(monkeypatch):
    def flaky_classify(X, model_name):
        if model_name == "svm":
            raise RuntimeError("model file missing")
        return {"results": [{"label": "other"}]}

    monkeypatch.setattr(cs, "_classify_locked", flaky_classify)
    monkeypatch.setattr(cs, "_get_available_models", lambda: ["svm", "mlp"])

    results = await cs._classify_all_models(np.zeros((1, 4)))

    assert list(results) == ["mlp"]
