from app.ml.config import MLConfig
from app.ml.registry import ModelRegistry
from app.ml.dataset import generate_synthetic_dataset, train_test_split_data
from app.ml.classifiers.tier2.mlp import MLPClassifier
from app.ml.classifiers.tier2.cnn1d import CNN1DClassifier
from app.ml.classifiers.tier2.lstm import LSTMClassifier
from app.ml.classifiers.tier2.transformer import TransformerClassifier
from app.ml.evaluation.report import ReportGenerator


def test_all_tier2_classifiers():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=300, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    registry = ModelRegistry()
    registry.register(MLPClassifier())
    registry.register(CNN1DClassifier())
    registry.register(LSTMClassifier())
    registry.register(TransformerClassifier())

    assert len(registry.all()) == 4
    assert len(registry.list_by_tier("tier2")) == 4

    generator = ReportGenerator(classifiers=registry.all(), config=config)
    report = generator.run(X_train, y_train, X_test, y_test)

    assert len(report.comparison_table) == 4
    for m in report.comparison_table:
        assert m.accuracy > 0.0
        assert m.f1_macro > 0.0
        assert m.tier == "tier2"

    print("\n=== TIER 2 COMPARATIVE TABLE ===\n")
    generator.print_comparison_table(report)


if __name__ == "__main__":
    test_all_tier2_classifiers()
