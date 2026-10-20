from app.ml.config import MLConfig, ACTIVITY_LABELS
from app.ml.dataset import generate_synthetic_dataset
from app.ml.evaluation.embeddings import compute_tsne, print_embedding_stats


def test_tsne():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)

    result = compute_tsne(X, y, label_names=ACTIVITY_LABELS)

    assert result.method == "t-SNE"
    # 200 samples split evenly across the classes, so the count is a multiple of NUM_CLASSES.
    assert result.coordinates.shape == (len(y), 2)
    assert len(result.labels) == len(y)
    assert len(result.label_names) == len(ACTIVITY_LABELS)

    print_embedding_stats(result)
