from app.ml.config import MLConfig, ACTIVITY_LABELS
from app.ml.dataset import generate_synthetic_dataset
from app.ml.evaluation.embeddings import compute_tsne, print_embedding_stats


def test_tsne():
    config = MLConfig()
    X, y = generate_synthetic_dataset(n_samples=200, n_features=50, config=config)

    result = compute_tsne(X, y, label_names=ACTIVITY_LABELS)

    assert result.method == "t-SNE"
    assert result.coordinates.shape == (200, 2)
    assert len(result.labels) == 200
    assert len(result.label_names) == 10

    print_embedding_stats(result)
