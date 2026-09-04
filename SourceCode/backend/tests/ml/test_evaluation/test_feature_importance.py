from app.ml.config import MLConfig
from app.ml.dataset import generate_synthetic_dataset, train_test_split_data
from app.ml.classifiers.tier1.svm import SVMClassifier
from app.ml.evaluation.feature_importance import compute_feature_importance, print_feature_importance


def test_feature_importance():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)
    X_train, X_test, y_train, y_test = train_test_split_data(X, y, config=config)

    clf = SVMClassifier()
    clf.fit(X_train, y_train)

    result = compute_feature_importance(clf, X_test, y_test, n_repeats=5, top_k=10)

    assert result.model_name == "svm"
    assert result.method == "permutation"
    assert len(result.top_k_indices) == 10
    assert len(result.top_k_means) == 10
    assert result.importances_mean[0] >= result.importances_mean[1]

    print_feature_importance(result)
