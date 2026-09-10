from app.ml.base import BaseClassifier


class ModelRegistry:

    def __init__(self) -> None:
        self._models: dict[str, BaseClassifier] = {}

    def register(self, model: BaseClassifier) -> None:
        self._models[model.name] = model

    def get(self, name: str) -> BaseClassifier:
        if name not in self._models:
            raise KeyError(f"Model '{name}' not registered")
        return self._models[name]

    def list_by_tier(self, tier: str) -> list[BaseClassifier]:
        return [m for m in self._models.values() if m.tier == tier]

    def all(self) -> list[BaseClassifier]:
        return list(self._models.values())

    def names(self) -> list[str]:
        return list(self._models.keys())
