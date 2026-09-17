import numpy as np
import pytest
from pathlib import Path

from app.ml.config import ACTIVITY_LABELS, MLConfig
from app.ml.dataset_loader import (
    ActionRecord,
    TaskMetadata,
    derive_activity_label,
    discover_tasks,
    task_level_split,
)
from app.pipeline.video_processor import VideoProcessor, FrameData, SegmentData
from app.pipeline.interaction_features import InteractionFeatureExtractor, INTERACTION_FEATURE_DIM
from app.pipeline.visual_features import VisualFeatureExtractor, VISUAL_FEATURE_DIM
from app.pipeline.temporal_encoder import TemporalEncoder
from app.pipeline.augmentation import augment_features
from app.pipeline.feature_assembler import MODALITY_MAP, TOTAL_FEATURES


DATASET_ROOT = Path(__file__).resolve().parents[3] / "dataset"
SAMPLE_VIDEO = DATASET_ROOT / "91097" / "video" / "video.mp4"


class TestDeriveActivityLabel:
    def test_git_keywords(self):
        assert derive_activity_label("git clone the repository") == "git_operations"
        assert derive_activity_label("push changes to branch") == "git_operations"

    def test_coding_keywords(self):
        assert derive_activity_label("Install language Extension python") == "coding_editing"
        assert derive_activity_label("Open file and edit code") == "coding_editing"

    def test_docker_keywords(self):
        assert derive_activity_label("Build a Docker image") == "docker_workflow"

    def test_debug_keywords(self):
        assert derive_activity_label("Set a breakpoint and inspect") == "debugging"

    def test_fallback(self):
        assert derive_activity_label("some random text") == "other"

    def test_platform_influence(self):
        assert derive_activity_label("open project settings", "NetBeans") == "coding_editing"


class TestDiscoverTasks:
    @pytest.mark.skipif(not DATASET_ROOT.exists(), reason="Dataset not available")
    def test_discover_finds_tasks(self):
        tasks = discover_tasks(DATASET_ROOT)
        assert len(tasks) > 0
        assert all(isinstance(t, TaskMetadata) for t in tasks)

    @pytest.mark.skipif(not DATASET_ROOT.exists(), reason="Dataset not available")
    def test_task_has_required_fields(self):
        tasks = discover_tasks(DATASET_ROOT)
        for t in tasks:
            assert t.task_id > 0
            assert t.instruction
            assert t.platform
            assert t.activity_label in ACTIVITY_LABELS
            assert len(t.actions) > 0

    @pytest.mark.skipif(not DATASET_ROOT.exists(), reason="Dataset not available")
    def test_video_task_has_path(self):
        tasks = discover_tasks(DATASET_ROOT)
        video_tasks = [t for t in tasks if t.video_path is not None]
        assert len(video_tasks) >= 1
        assert video_tasks[0].video_path.exists()


class TestTaskLevelSplit:
    def test_split_preserves_all_tasks(self):
        tasks = [
            TaskMetadata(
                task_id=i, instruction=f"task {i}", platform="test",
                video_path=None, actions=[], video_meta=None,
                activity_label="coding_editing", workflow=f"task {i}",
            )
            for i in range(10)
        ]
        train, test = task_level_split(tasks, test_ratio=0.2, seed=42)
        assert len(train) + len(test) == len(tasks)
        assert len(test) >= 1

    def test_split_no_overlap(self):
        tasks = [
            TaskMetadata(
                task_id=i, instruction=f"task {i}", platform="test",
                video_path=None, actions=[], video_meta=None,
                activity_label="coding_editing" if i < 7 else "other",
                workflow=f"task {i}",
            )
            for i in range(10)
        ]
        train, test = task_level_split(tasks, test_ratio=0.3, seed=42)
        train_ids = {t.task_id for t in train}
        test_ids = {t.task_id for t in test}
        assert train_ids.isdisjoint(test_ids)


class TestVideoProcessor:
    @pytest.mark.skipif(not SAMPLE_VIDEO.exists(), reason="Sample video not available")
    def test_get_metadata(self):
        vp = VideoProcessor()
        meta = vp.get_metadata(SAMPLE_VIDEO)
        assert meta["fps"] > 0
        assert meta["duration_seconds"] > 0
        assert meta["width"] > 0
        assert meta["height"] > 0

    @pytest.mark.skipif(not SAMPLE_VIDEO.exists(), reason="Sample video not available")
    def test_extract_frames(self):
        vp = VideoProcessor(sample_fps=1.0)
        frames = vp.extract_frames(SAMPLE_VIDEO)
        assert len(frames) > 0
        assert all(isinstance(f, FrameData) for f in frames)
        assert frames[0].image.shape == (480, 640, 3)

    @pytest.mark.skipif(not SAMPLE_VIDEO.exists(), reason="Sample video not available")
    def test_extract_segments_with_actions(self):
        vp = VideoProcessor()
        actions = [
            {"action_type": "CLICK", "timestamp": 5.0, "action_params": {"x": 100, "y": 200}},
            {"action_type": "TYPING", "timestamp": 6.5, "action_params": {"text": "hello"}},
            {"action_type": "CLICK", "timestamp": 15.0, "action_params": {"x": 300, "y": 400}},
        ]
        segments = vp.extract_segments(SAMPLE_VIDEO, actions)
        assert len(segments) >= 2
        assert all(isinstance(s, SegmentData) for s in segments)
        assert all(len(s.keyframes) > 0 for s in segments)


class TestInteractionFeatures:
    def test_output_shape(self):
        extractor = InteractionFeatureExtractor()
        actions = [
            ActionRecord(action_type="CLICK", timestamp=1.0, params={"x": 100, "y": 200}),
            ActionRecord(action_type="TYPING", timestamp=2.0, params={"text": "hello"}),
            ActionRecord(action_type="MOVE_TO", timestamp=3.0, params={"x": 300, "y": 400}),
        ]
        features = extractor.extract(actions, 0.0, 5.0)
        assert features.shape == (INTERACTION_FEATURE_DIM,)
        assert features.dtype == np.float32

    def test_empty_actions(self):
        extractor = InteractionFeatureExtractor()
        features = extractor.extract([], 0.0, 5.0)
        assert features.shape == (INTERACTION_FEATURE_DIM,)
        assert np.all(features == 0.0)

    def test_values_normalized(self):
        extractor = InteractionFeatureExtractor()
        actions = [
            ActionRecord(action_type="CLICK", timestamp=1.0, params={"x": 100, "y": 200}),
            ActionRecord(action_type="CLICK", timestamp=2.0, params={"x": 500, "y": 600}),
        ]
        features = extractor.extract(actions, 0.0, 5.0)
        assert np.all(features >= -1.0)
        assert np.all(features <= 1.0)


class TestVisualFeatures:
    def test_output_shape(self):
        extractor = VisualFeatureExtractor()
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        features = extractor.extract(image)
        assert features.shape == (VISUAL_FEATURE_DIM,)
        assert features.dtype == np.float32

    def test_empty_image(self):
        extractor = VisualFeatureExtractor()
        features = extractor.extract(np.array([]))
        assert features.shape == (VISUAL_FEATURE_DIM,)
        assert np.all(features == 0.0)

    def test_segment_averaging(self):
        extractor = VisualFeatureExtractor()
        kf1 = FrameData(frame_index=0, timestamp=0.0, image=np.zeros((480, 640, 3), dtype=np.uint8))
        kf2 = FrameData(frame_index=1, timestamp=1.0, image=np.ones((480, 640, 3), dtype=np.uint8) * 255)
        features = extractor.extract_segment([kf1, kf2])
        assert features.shape == (VISUAL_FEATURE_DIM,)


class TestTemporalEncoder:
    def test_single_segment(self):
        encoder = TemporalEncoder()
        X = np.random.randn(1, 150).astype(np.float32)
        encoded = encoder.encode_sequence(X)
        np.testing.assert_array_equal(X, encoded)

    def test_multi_segment_blending(self):
        encoder = TemporalEncoder(window_size=1)
        X = np.random.randn(5, 150).astype(np.float32)
        encoded = encoder.encode_sequence(X)
        assert encoded.shape == X.shape
        assert not np.array_equal(X[2], encoded[2])


class TestAugmentation:
    def test_augment_multiplies_samples(self):
        X = np.random.randn(10, 150).astype(np.float32)
        y = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        X_aug, y_aug = augment_features(X, y, n_augmented=2)
        assert X_aug.shape[0] == 30
        assert y_aug.shape[0] == 30
        assert X_aug.shape[1] == 150

    def test_augment_preserves_labels(self):
        X = np.random.randn(10, 150).astype(np.float32)
        y = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        _, y_aug = augment_features(X, y, n_augmented=3)
        for label in range(10):
            assert np.sum(y_aug == label) == 4


class TestModalityMap:
    def test_covers_full_range(self):
        ranges = list(MODALITY_MAP.values())
        assert ranges[0][0] == 0
        for i in range(1, len(ranges)):
            assert ranges[i][0] == ranges[i - 1][1]
        assert ranges[-1][1] == TOTAL_FEATURES

    def test_total_features(self):
        assert TOTAL_FEATURES == 150

    def test_four_modalities(self):
        assert len(MODALITY_MAP) == 4
        assert "ocr_text" in MODALITY_MAP
        assert "ui_elements" in MODALITY_MAP
        assert "visual" in MODALITY_MAP
        assert "interaction" in MODALITY_MAP
