"""The bare-video SOP detector: the steps a user performed, from the screen recording alone.

This package is what runs in the service (sop_detector_service.py) and the container
(deploy/sop-detector). It has three parts:

    typed_text.py   name the application, then the "Type ..." steps
    clicks.py       the mouse pointer, where it stops, and the "Click '...'" steps
    pipeline.py     both, merged in time order: run(video) -> {app, steps, ...}

The rest of Evaluation/ is the research that built and scored it (bare_sop_v2.py is
the same detector written against the research scripts; pointer_cnn_eval_v2.py and
combined_sop_v3.py give the numbers in the README).
"""
from detector.pipeline import run

__all__ = ["run"]
