import numpy as np
import cv2
import pytest

from pipeline.geometry import GeometryCleanupPipeline

def test_process_layer_empty_mask():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    mask = np.zeros((100, 100), dtype=np.uint8)

    result = GeometryCleanupPipeline.process_layer(image, mask)

    assert result.shape == (100, 100, 4)
    assert np.all(result == 0)

def test_process_layer_solid_color():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[20:80, 20:80] = [255, 0, 0] # Blue square

    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 255

    result = GeometryCleanupPipeline.process_layer(image, mask)

    assert result.shape == (100, 100, 4)
    assert np.all(result[50, 50] == [255, 0, 0, 255])
    assert np.all(result[10, 10] == [0, 0, 0, 0])

def test_process_layer_multiple_colors():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[20:50, 20:80] = [255, 0, 0] # Blue
    image[50:80, 20:80] = [0, 255, 0] # Green

    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 255

    result = GeometryCleanupPipeline.process_layer(image, mask)

    assert result.shape == (100, 100, 4)
    assert np.all(result[30, 50] == [255, 0, 0, 255])
    assert np.all(result[60, 50] == [0, 255, 0, 255])
    assert np.all(result[10, 10] == [0, 0, 0, 0])

def test_process_layer_black_color_skipped():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 255

    result = GeometryCleanupPipeline.process_layer(image, mask)

    assert result.shape == (100, 100, 4)
    assert np.all(result == 0)
