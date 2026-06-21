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

@patch("cv2.grabCut")
def test_run_rt_detr_fallback_mask(mock_grabcut, inference_pipeline):
    h_orig, w_orig = 50, 50
    original_img = np.zeros((h_orig, w_orig, 3), dtype=np.uint8)
    bbox = (10, 10, 40, 40)

    # Mock grabcut behavior to simulate modifying the mask
    # cv2.GC_PR_BGD is 2, cv2.GC_PR_FGD is 3
    def mock_grabcut_side_effect(img, mask, rect, bgdModel, fgdModel, iterCount, mode):
        # Set all to probable background
        mask[:] = 2
        # Set a small region to probable foreground
        mask[20:30, 20:30] = 3

    mock_grabcut.side_effect = mock_grabcut_side_effect

    binary_mask = inference_pipeline.run_rt_detr_fallback_mask(original_img, bbox)

    # Validate grabCut was called with correct arguments
    assert mock_grabcut.called
    args, kwargs = mock_grabcut.call_args
    assert np.array_equal(args[0], original_img)
    assert args[2] == (10, 10, 30, 30) # rect format: x, y, w, h
    assert args[5] == 5 # iterCount
    # cv2.GC_INIT_WITH_RECT is 0
    import cv2
    assert args[6] == cv2.GC_INIT_WITH_RECT

    # Validate the resulting binary mask
    assert binary_mask.shape == (50, 50)
    assert binary_mask.dtype == np.uint8

    # Check that probable background (2) became 0
    assert binary_mask[10, 10] == 0

    # Check that probable foreground (3) became 255
    assert binary_mask[25, 25] == 255

def test_run_rt_detr_fallback_mask_mock_inference(inference_pipeline):
    with patch("pipeline.inference.MOCK_INFERENCE", True):
        h_orig, w_orig = 50, 50
        original_img = np.zeros((h_orig, w_orig, 3), dtype=np.uint8)
        bbox = (10, 10, 40, 40)

        binary_mask = inference_pipeline.run_rt_detr_fallback_mask(original_img, bbox)

        assert binary_mask.shape == (50, 50)
        assert binary_mask.dtype == np.uint8

        # Rectangular mask should be filled with 255 inside bbox
        assert binary_mask[20, 20] == 255
        # Background should be 0
        assert binary_mask[5, 5] == 0
