import pytest
import numpy as np
from unittest.mock import MagicMock, patch
import os

from pipeline.inference import AIInferencePipeline

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"MOCK_INFERENCE": "false"}):
        yield

@pytest.fixture
def inference_pipeline(mock_env):
    with patch("pipeline.inference.AIInferencePipeline._load_models"):
        pipeline = AIInferencePipeline()
        pipeline.rt_detr_session = MagicMock()
        pipeline.sam2_model = MagicMock()
        yield pipeline

def test_run_rt_detr_detection_success(inference_pipeline):
    # Setup mock image
    h_orig, w_orig = 100, 100
    original_img = np.zeros((h_orig, w_orig, 3), dtype=np.uint8)

    # Box 1: High confidence (xc=0.5, yc=0.5, w=0.2, h=0.2, conf=0.9, class0=0.9)
    # Box 2: Low confidence (xc=0.1, yc=0.1, w=0.1, h=0.1, conf=0.2, class0=0.2)
    mock_predictions = np.array([
        [
            [0.5, 0.5, 0.2, 0.2, 0.9, 0.9],
            [0.1, 0.1, 0.1, 0.1, 0.2, 0.2]
        ]
    ], dtype=np.float32)

    inference_pipeline.rt_detr_session.get_inputs.return_value = [MagicMock(name="input0")]
    inference_pipeline.rt_detr_session.run.return_value = [mock_predictions]

    bboxes = inference_pipeline.run_rt_detr_detection(original_img)

    assert len(bboxes) == 1
    assert bboxes[0] == (40, 40, 60, 60)

def test_run_rt_detr_detection_no_valid_boxes(inference_pipeline):
    h_orig, w_orig = 100, 100
    original_img = np.zeros((h_orig, w_orig, 3), dtype=np.uint8)

    # All low confidence
    mock_predictions = np.array([
        [
            [0.5, 0.5, 0.2, 0.2, 0.2, 0.2],
        ]
    ], dtype=np.float32)

    inference_pipeline.rt_detr_session.get_inputs.return_value = [MagicMock(name="input0")]
    inference_pipeline.rt_detr_session.run.return_value = [mock_predictions]

    bboxes = inference_pipeline.run_rt_detr_detection(original_img)

    assert len(bboxes) == 0

def test_run_rt_detr_detection_none_image(inference_pipeline):
    with pytest.raises(ValueError, match="Provided image array is None."):
        inference_pipeline.run_rt_detr_detection(None)

def test_run_rt_detr_detection_no_session():
    with patch("pipeline.inference.AIInferencePipeline._load_models"):
        with patch.dict(os.environ, {"MOCK_INFERENCE": "false"}):
            pipeline = AIInferencePipeline()
            pipeline.rt_detr_session = None
            with pytest.raises(RuntimeError, match="RT-DETR session not loaded."):
                pipeline.run_rt_detr_detection(np.zeros((100, 100, 3), dtype=np.uint8))

def test_run_rt_detr_detection_invalid_shape(inference_pipeline):
    h_orig, w_orig = 100, 100
    original_img = np.zeros((h_orig, w_orig, 3), dtype=np.uint8)

    # Invalid shape: < 6 fields
    mock_predictions = np.array([
        [
            [0.5, 0.5, 0.2, 0.2, 0.9],
        ]
    ], dtype=np.float32)

    inference_pipeline.rt_detr_session.get_inputs.return_value = [MagicMock(name="input0")]
    inference_pipeline.rt_detr_session.run.return_value = [mock_predictions]

    bboxes = inference_pipeline.run_rt_detr_detection(original_img)

    assert len(bboxes) == 0
