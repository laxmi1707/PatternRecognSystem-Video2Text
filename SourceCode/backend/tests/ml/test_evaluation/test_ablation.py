from app.ml.config import MLConfig
from app.ml.dataset import generate_synthetic_dataset, train_test_split_data
from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
from app.ml.evaluation.ablation import run_ablation_study, print_ablation_results


def test_ablation_default_modalities():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    result = run_ablation_study(
        RandomForestClassifier(), X_train, y_train, X_test, y_test,
    )

    assert result.model_name == "random_forest"
    assert result.baseline_f1 > 0.0
    assert len(result.ablations) == 5
    for a in result.ablations:
        assert a.f1_without >= 0.0
        assert a.f1_drop >= -1.0

    print_ablation_results(result)


def test_ablation_custom_modalities():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    modality_map = {
        "ocr_text": (0, 20),
        "ui_labels": (20, 35),
        "cursor": (35, 50),
    }
    result = run_ablation_study(
        RandomForestClassifier(), X_train, y_train, X_test, y_test,
        modality_map=modality_map,
    )

    assert len(result.ablations) == 3
    names = [a.modality_name for a in result.ablations]
    assert "ocr_text" in names
    assert "ui_labels" in names
    assert "cursor" in names
