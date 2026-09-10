from app.ml.config import MLConfig
from app.ml.registry import ModelRegistry
from app.ml.dataset import generate_synthetic_dataset, train_test_split_data
from app.ml.classifiers.tier1.svm import SVMClassifier
from app.ml.classifiers.tier1.naive_bayes import NaiveBayesClassifier
from app.ml.classifiers.tier1.decision_tree import DecisionTreeClassifier
from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
from app.ml.classifiers.tier1.knn import KNNClassifier
from app.ml.classifiers.tier1.xgboost_clf import XGBoostClassifier
from app.ml.classifiers.tier1.lightgbm_clf import LightGBMClassifier
from app.ml.evaluation.report import ReportGenerator


def test_all_tier1_classifiers():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=300, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    registry = ModelRegistry()
    registry.register(SVMClassifier())
    registry.register(NaiveBayesClassifier())
    registry.register(DecisionTreeClassifier())
    registry.register(RandomForestClassifier())
    registry.register(KNNClassifier())
    registry.register(XGBoostClassifier())
    registry.register(LightGBMClassifier())

    assert len(registry.all()) == 7
    assert len(registry.list_by_tier("tier1")) == 7

    generator = ReportGenerator(classifiers=registry.all(), config=config)
    report = generator.run(X_train, y_train, X_test, y_test)

    assert len(report.comparison_table) == 7
    for m in report.comparison_table:
        assert m.accuracy > 0.0
        assert m.f1_macro > 0.0
        assert m.tier == "tier1"

    print("\n=== TIER 1 COMPARATIVE TABLE ===\n")
    generator.print_comparison_table(report)


if __name__ == "__main__":
    test_all_tier1_classifiers()
