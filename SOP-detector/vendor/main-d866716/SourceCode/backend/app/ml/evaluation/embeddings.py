from dataclasses import dataclass

import numpy as np
from sklearn.manifold import TSNE


@dataclass(frozen=True)
class EmbeddingResult:
    method: str
    coordinates: np.ndarray
    labels: np.ndarray
    label_names: tuple[str, ...]


def compute_tsne(
    X: np.ndarray,
    y: np.ndarray,
    label_names: tuple[str, ...] | list[str],
    n_components: int = 2,
    perplexity: float = 30.0,
    seed: int = 42,
) -> EmbeddingResult:
    tsne = TSNE(
        n_components=n_components,
        perplexity=min(perplexity, max(5.0, len(X) / 4)),
        random_state=seed,
        init="pca",
        learning_rate="auto",
    )
    coords = tsne.fit_transform(X)

    return EmbeddingResult(
        method="t-SNE",
        coordinates=coords,
        labels=y,
        label_names=tuple(label_names),
    )


def compute_umap(
    X: np.ndarray,
    y: np.ndarray,
    label_names: tuple[str, ...] | list[str],
    n_components: int = 2,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    seed: int = 42,
) -> EmbeddingResult:
    try:
        import umap
    except ImportError:
        raise ImportError("umap-learn is not installed. Install with: pip install umap-learn")

    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=seed,
    )
    coords = reducer.fit_transform(X)

    return EmbeddingResult(
        method="UMAP",
        coordinates=coords,
        labels=y,
        label_names=tuple(label_names),
    )


def print_embedding_stats(result: EmbeddingResult) -> None:
    print(f"\n{result.method} Embedding ({result.coordinates.shape[1]}D):")
    print(f"  Samples: {len(result.labels)}")
    print(f"  Classes: {len(result.label_names)}")
    for i, name in enumerate(result.label_names):
        mask = result.labels == i
        if mask.sum() > 0:
            centroid = result.coordinates[mask].mean(axis=0)
            spread = result.coordinates[mask].std()
            print(f"  {name:<20} n={mask.sum():<4} centroid=({centroid[0]:>6.1f}, {centroid[1]:>6.1f})  spread={spread:.2f}")
