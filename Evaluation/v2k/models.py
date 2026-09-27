"""The backend's 14 classifiers, built as MLService registers them, plus AdaBoost.

AdaBoost is not one of the backend's 14; it lives in v2k/adaboost.py and is
included so the comparison covers the boosting scheme that XGBoost and LightGBM
descend from. Anywhere it appears in a table it has to be marked as an addition
on our side - BACKEND_MODELS is the set the team actually ships.

One deliberate difference: the torch models get num_classes = the number of
classes actually trained on. The backend hard-codes 10, while its sklearn
models only output columns for the classes they saw, which is what breaks
MLService.classify for 10 of the 14 models.
"""
from __future__ import annotations

BACKEND_MODELS = (
    "svm", "naive_bayes", "decision_tree", "random_forest", "knn", "xgboost", "lightgbm",
    "mlp", "cnn1d", "lstm", "transformer",
    "voting", "stacking", "late_fusion",
)
# Ours, not the backend's. Kept separate so a report can never imply otherwise.
ADDED_MODELS = ("adaboost",)
MODEL_NAMES = BACKEND_MODELS + ADDED_MODELS
TIER = {
    **{m: "tier1" for m in BACKEND_MODELS[:7]},
    **{m: "tier2" for m in BACKEND_MODELS[7:11]},
    **{m: "tier3" for m in BACKEND_MODELS[11:]},
    "adaboost": "tier1",
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

    def _adaboost():
        from v2k.adaboost import AdaBoostClassifier

        return AdaBoostClassifier()

    k = {"num_classes": n_classes}
    builders = {
        "svm": lambda: SVMClassifier(),
        "naive_bayes": lambda: NaiveBayesClassifier(),
        "decision_tree": lambda: DecisionTreeClassifier(),
        "random_forest": lambda: RandomForestClassifier(),
        "knn": lambda: KNNClassifier(),
        "xgboost": lambda: XGBoostClassifier(),
        "lightgbm": lambda: LightGBMClassifier(),
        "adaboost": lambda: _adaboost(),
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
    if names == ["backend"]:
        return list(BACKEND_MODELS)
    for n in names:
        if n not in MODEL_NAMES:
            raise SystemExit(f"unknown model '{n}' (known: {', '.join(MODEL_NAMES)})")
    return names
