from app.ml.config import MLConfig
from app.ml.dataset import generate_synthetic_dataset
from app.ml.classifiers.tier1.svm import SVMClassifier
from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
from app.ml.classifiers.tier2.mlp import MLPClassifier
from app.ml.evaluation.cross_validation import CVResult, cross_validate, print_cv_results


def test_cross_validate_single_model():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)

    result = cross_validate(SVMClassifier(), X, y, config=config)

    assert isinstance(result, CVResult)
    assert result.model_name == "svm"
    assert result.tier == "tier1"
    assert result.n_folds == 5
    assert len(result.fold_metrics) == 5
    assert 0.0 < result.mean_accuracy <= 1.0
    assert 0.0 < result.mean_f1 <= 1.0
    assert 0.0 < result.mean_auc <= 1.0
    assert result.std_accuracy >= 0.0
    assert result.mean_latency_ms > 0.0


def test_cross_validate_multiple_models():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)

    classifiers = [SVMClassifier(), RandomForestClassifier(), MLPClassifier()]
    results = [cross_validate(clf, X, y, config=config) for clf in classifiers]

    assert len(results) == 3
    names = [r.model_name for r in results]
    assert "svm" in names
    assert "random_forest" in names
    assert "mlp" in names

    for r in results:
        assert r.n_folds == 5
        assert r.mean_f1 > 0.5

    print("\n=== CROSS-VALIDATION RESULTS ===\n")
    print_cv_results(results)
