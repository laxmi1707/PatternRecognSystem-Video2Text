"""The 14 classifiers the frontend's dropdown offers, built as MLService registers them.

One deliberate difference: the torch models get num_classes = the number of
classes actually trained on. The backend hard-codes 10, while its sklearn
models only output columns for the classes they saw, which is what breaks
MLService.classify for 10 of the 14 models.
"""
from __future__ import annotations

MODEL_NAMES = (
    "svm", "naive_bayes", "decision_tree", "random_forest", "knn", "xgboost", "lightgbm",
    "mlp", "cnn1d", "lstm", "transformer",
    "voting", "stacking", "late_fusion",
)
TIER = {
    **{m: "tier1" for m in MODEL_NAMES[:7]},
    **{m: "tier2" for m in MODEL_NAMES[7:11]},
    **{m: "tier3" for m in MODEL_NAMES[11:]},
}


def make(name: str, n_classes: int):
    from app.ml.classifiers.tier1.decision_tree import DecisionTreeClassifier
    from app.ml.classifiers.tier1.knn import KNNClassifier
    from app.ml.classifiers.tier1.lightgbm_clf import LightGBMClassifier
    from app.ml.classifiers.tier1.naive_bayes import NaiveBayesClassifier
    from app.ml.classifiers.tier1.random_forest import RandomForestClassifier
    from app.ml.classifiers.tier1.svm import SVMClassifier
    from app.ml.classifiers.tier1.xgboost_clf import XGBoostClassifier
    from app.ml.classifiers.tier2 import CNN1DClassifier, LSTMClassifier, MLPClassifier, TransformerClassifier
    from app.ml.classifiers.tier3 import LateFusionClassifier, StackingClassifier, VotingClassifier

    k = {"num_classes": n_classes}
    builders = {
        "svm": lambda: SVMClassifier(),
        "naive_bayes": lambda: NaiveBayesClassifier(),
        "decision_tree": lambda: DecisionTreeClassifier(),
        "random_forest": lambda: RandomForestClassifier(),
        "knn": lambda: KNNClassifier(),
        "xgboost": lambda: XGBoostClassifier(),
        "lightgbm": lambda: LightGBMClassifier(),
        "mlp": lambda: MLPClassifier(**k),
        "cnn1d": lambda: CNN1DClassifier(**k),
        "lstm": lambda: LSTMClassifier(**k),
        "transformer": lambda: TransformerClassifier(**k),
        "voting": lambda: VotingClassifier(
            estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier(**k)], voting="soft",
        ),
        "stacking": lambda: StackingClassifier(
            base_estimators=[SVMClassifier(), RandomForestClassifier(), MLPClassifier(**k)],
        ),
        "late_fusion": lambda: LateFusionClassifier(branches=[SVMClassifier(), RandomForestClassifier()]),
    }
    if name not in builders:
        raise SystemExit(f"unknown model '{name}' (known: {', '.join(MODEL_NAMES)})")
    return builders[name]()


def parse_models(names: list[str]) -> list[str]:
    if names == ["all"]:
        return list(MODEL_NAMES)
    for n in names:
        if n not in MODEL_NAMES:
            raise SystemExit(f"unknown model '{n}' (known: {', '.join(MODEL_NAMES)})")
    return names
