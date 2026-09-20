from __future__ import annotations

import random

from app.data_pipeline.types import DatasetSplits, LabeledExample


def split_dataset(
    examples: list[LabeledExample],
    train_ratio: float = 0.7,
    validation_ratio: float = 0.15,
    seed: int = 42,
) -> DatasetSplits:
    shuffled = list(examples)
    random.Random(seed).shuffle(shuffled)

    n = len(shuffled)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * validation_ratio)

    return DatasetSplits(
        train=tuple(shuffled[:train_end]),
        validation=tuple(shuffled[train_end:val_end]),
        test=tuple(shuffled[val_end:]),
    )
