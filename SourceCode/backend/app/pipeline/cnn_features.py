from __future__ import annotations

import logging
import threading

import cv2
import numpy as np

logger = logging.getLogger(__name__)

CNN_FEATURE_DIM = 1280  # EfficientNet-B0 final embedding size

# One EfficientNet per process and device, shared by every job (each job builds its own
# FeatureAssembler). The weights ship in the image (Dockerfile), so loading reads no network.
_MODELS: dict[str, tuple] = {}
_MODEL_LOCK = threading.Lock()


class CNNFeatureExtractor:
    """EfficientNet-B0 frame embeddings via torchvision (pretrained on ImageNet).

    Replaces hand-crafted HOG/color features with learned visual representations
    that generalise to unseen screen recordings without action log data.
    """

    def __init__(self, use_gpu: bool = False):
        self._use_gpu = use_gpu
        self._model = None
        self._preprocess = None

    def _load_model(self):
        if self._model is not None:
            return
        try:
            import torch
            import torchvision.models as models
        except ImportError as e:
            logger.warning(f"torchvision not available, CNN features will be zeros: {e}")
            return

        device = torch.device("cuda" if self._use_gpu and torch.cuda.is_available() else "cpu")
        with _MODEL_LOCK:
            if str(device) not in _MODELS:
                weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
                model = models.efficientnet_b0(weights=weights)
                # Remove classifier head — keep feature extractor only
                model.classifier = torch.nn.Identity()
                model.eval()
                _MODELS[str(device)] = (model.to(device), weights.transforms())
                print(f"[CNN] EfficientNet-B0 loaded on {device}", flush=True)
            self._model, self._preprocess = _MODELS[str(device)]
        self._device = device

    def extract(self, image: np.ndarray) -> np.ndarray:
        """Extract 1280-dim EfficientNet embedding from one BGR frame."""
        self._load_model()
        if self._model is None:
            return np.zeros(CNN_FEATURE_DIM, dtype=np.float32)

        import torch
        from PIL import Image

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        tensor = self._preprocess(pil_img).unsqueeze(0).to(self._device)

        with torch.no_grad():
            embedding = self._model(tensor).squeeze(0).cpu().numpy()

        return embedding.astype(np.float32)

    def extract_segment(self, keyframes: list) -> np.ndarray:
        """Average EfficientNet embeddings across all keyframes in a segment."""
        if not keyframes:
            return np.zeros(CNN_FEATURE_DIM, dtype=np.float32)

        embeddings = [self.extract(kf.image) for kf in keyframes]
        return np.mean(embeddings, axis=0).astype(np.float32)
