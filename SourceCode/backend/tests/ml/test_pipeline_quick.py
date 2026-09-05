from app.ml.base import BaseClassifier, PredictionResult
from app.ml.config import MLConfig, ACTIVITY_LABELS
from app.ml.registry import ModelRegistry
from app.ml.dataset import generate_synthetic_dataset, train_test_split_data
from app.ml.classifiers.tier1.svm import SVMClassifier
from app.ml.evaluation.report import ReportGenerator


def test_full_pipeline():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    registry = ModelRegistry()
    registry.register(SVMClassifier())

    generator = ReportGenerator(classifiers=registry.all(), config=config)
    report = generator.run(X_train, y_train, X_test, y_test)

    assert len(report.comparison_table) == 1
    assert report.comparison_table[0].model_name == "svm"
    assert report.comparison_table[0].accuracy > 0.0
    assert "svm" in report.confusion_matrices
    assert "svm" in report.roc_curves

    generator.print_comparison_table(report)
    print("\nAll tests passed!")


if __name__ == "__main__":
    test_full_pipeline()
