from app.ml.config import MLConfig
from app.ml.registry import ModelRegistry
from app.ml.dataset import generate_synthetic_dataset, train_test_split_data
from app.ml.classifiers.tier1.svm import SVMClassifier
from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
from app.ml.classifiers.tier2.mlp import MLPClassifier
from app.ml.classifiers.tier3.voting import VotingClassifier
from app.ml.classifiers.tier3.stacking import StackingClassifier
from app.ml.classifiers.tier3.late_fusion import LateFusionClassifier
from app.ml.evaluation.report import ReportGenerator


def test_voting_soft():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    clf = VotingClassifier(
        estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier()],
        voting="soft",
    )
    clf.fit(X_train, y_train)
    result = clf.predict(X_test)

    assert result.labels.shape[0] == X_test.shape[0]
    assert result.probabilities.shape == (X_test.shape[0], config.num_classes)
    assert result.latency_ms > 0


def test_voting_hard():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    clf = VotingClassifier(
        estimators=[SVMClassifier(), RandomForestClassifier()],
        voting="hard",
    )
    clf.fit(X_train, y_train)
    result = clf.predict(X_test)

    assert result.labels.shape[0] == X_test.shape[0]


def test_stacking():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    clf = StackingClassifier(
        base_estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier()],
    )
    clf.fit(X_train, y_train)
    result = clf.predict(X_test)

    assert result.labels.shape[0] == X_test.shape[0]
    assert result.probabilities.shape == (X_test.shape[0], config.num_classes)
    assert result.latency_ms > 0


def test_late_fusion():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    clf = LateFusionClassifier(
        branches=[SVMClassifier(), RandomForestClassifier()],
    )
    clf.fit(X_train, y_train)
    result = clf.predict(X_test)

    assert result.labels.shape[0] == X_test.shape[0]
    assert result.probabilities.shape == (X_test.shape[0], config.num_classes)
    assert result.latency_ms > 0


def test_all_tier3_comparative():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=300, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    base_models = [SVMClassifier(), RandomForestClassifier(), MLPClassifier()]

    registry = ModelRegistry()
    registry.register(VotingClassifier(estimators=base_models, voting="soft"))
    registry.register(StackingClassifier(base_estimators=base_models))
    registry.register(LateFusionClassifier(
        branches=[SVMClassifier(), RandomForestClassifier()],
    ))

    assert len(registry.all()) == 3
    assert len(registry.list_by_tier("tier3")) == 3

    generator = ReportGenerator(classifiers=registry.all(), config=config)
    report = generator.run(X_train, y_train, X_test, y_test)

    assert len(report.comparison_table) == 3
    for m in report.comparison_table:
        assert m.accuracy > 0.0
        assert m.f1_macro > 0.0
        assert m.tier == "tier3"

    print("\n=== TIER 3 COMPARATIVE TABLE ===\n")
    generator.print_comparison_table(report)


if __name__ == "__main__":
    test_all_tier3_comparative()
