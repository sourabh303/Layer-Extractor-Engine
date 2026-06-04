import numpy as np
import pytest
from unittest.mock import patch
from pipeline.inference import AIInferencePipeline

def test_run_rt_detr_fallback_mask_mocked():
    with patch("pipeline.inference.MOCK_INFERENCE", True):
        pipeline = AIInferencePipeline()
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        bbox = (2, 2, 8, 8)

        mask = pipeline.run_rt_detr_fallback_mask(img, bbox)
        assert mask.shape == (10, 10)
        assert mask.dtype == np.uint8
        # Mock returns 255 in the bbox
        assert mask[5, 5] == 255
        assert mask[0, 0] == 0

@patch("pipeline.inference.MOCK_INFERENCE", False)
@patch.object(AIInferencePipeline, "_load_models")
def test_run_rt_detr_fallback_mask_real(mock_load):
    pipeline = AIInferencePipeline()

    img = np.zeros((20, 20, 3), dtype=np.uint8)
    # Make foreground
    img[5:15, 5:15] = [255, 255, 255]
    bbox = (4, 4, 16, 16)

    mask = pipeline.run_rt_detr_fallback_mask(img, bbox)

    assert mask.shape == (20, 20)
    assert mask.dtype == np.uint8
    assert np.all(np.isin(mask, [0, 255]))
