"""Startup warm-up loads the OCR reader and survives a failing load."""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app.pipeline import ocr_extractor
from app.services.warmup import warm_up


@pytest.fixture(autouse=True)
def stub_ml_service(monkeypatch):
    # The real ml_service downloads and loads the models; warm-up only needs to import it.
    monkeypatch.setitem(
        sys.modules, "app.services.ml_service", SimpleNamespace(ml_service=SimpleNamespace(_trained_models={"svm"}))
    )


def test_warm_up_loads_the_shared_ocr_reader(monkeypatch):
    loaded = []
    monkeypatch.setattr(ocr_extractor.OCRExtractor, "_get_reader", lambda self: loaded.append(self) or object())

    warm_up()

    assert len(loaded) == 1


def test_warm_up_does_not_raise_when_a_load_fails(monkeypatch):
    def broken(self):
        raise RuntimeError("no network")

    monkeypatch.setattr(ocr_extractor.OCRExtractor, "_get_reader", broken)

    warm_up()  # logged as a warning; the first job loads the reader itself


def test_warm_up_loads_the_cnn_model_only_for_the_cnn_backend(monkeypatch):
    from app.pipeline import cnn_features, feature_assembler

    monkeypatch.setattr(ocr_extractor.OCRExtractor, "_get_reader", lambda self: object())
    loaded = []
    monkeypatch.setattr(cnn_features.CNNFeatureExtractor, "_load_model", lambda self: loaded.append(self))

    monkeypatch.setattr(feature_assembler, "FEATURE_BACKEND", "hog")
    warm_up()
    assert loaded == []

    monkeypatch.setattr(feature_assembler, "FEATURE_BACKEND", "cnn")
    warm_up()
    assert len(loaded) == 1
