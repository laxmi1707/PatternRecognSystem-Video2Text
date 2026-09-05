from app.ml.config import MLConfig, ACTIVITY_LABELS
from app.ml.dataset import generate_synthetic_dataset, train_test_split_data
from app.ml.classifiers.tier1.decision_tree import DecisionTreeClassifier
from app.ml.evaluation.error_analysis import run_error_analysis, print_error_analysis


def test_error_analysis():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    clf = DecisionTreeClassifier()
    clf.fit(X_train, y_train)

    result = run_error_analysis(clf, X_test, y_test, label_names=ACTIVITY_LABELS)

    assert result.model_name == "decision_tree"
    assert result.total_samples == len(y_test)
    assert result.total_errors >= 0
    assert 0.0 <= result.error_rate <= 1.0
    assert len(result.per_class_error_rate) == 10

    for m in result.worst_misclassifications:
        assert m.true_label != m.predicted_label
        assert 0.0 <= m.confidence <= 1.0

    print_error_analysis(result)
