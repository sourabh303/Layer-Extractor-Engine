import asyncio
import numpy as np
import sys
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Add the ml-service directory to the python path so we can import from main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["IPC_SECRET"] = "test_secret"

from main import app

client = TestClient(app, headers={"X-IPC-Secret": "test_secret"})

def test_authentication_missing_header():
    # Create a client that doesn't include the header
    no_auth_client = TestClient(app)
    response = no_auth_client.get("/status")
    assert response.status_code == 401
    assert "Missing X-IPC-Secret header" in response.json()["detail"]

def test_authentication_invalid_header():
    invalid_auth_client = TestClient(app, headers={"X-IPC-Secret": "wrong_secret"})
    response = invalid_auth_client.get("/status")
    assert response.status_code == 401
    assert "Invalid IPC Secret" in response.json()["detail"]

@patch('main.get_hardware_mode', return_value="CPU")
def test_extract_file_not_found(mock_get_hardware_mode):
    response = client.post(
        "/extract",
        json={"source_path": "/invalid/path/that/does/not/exist.jpg"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "error"
    assert data["message"] == "File not found: /invalid/path/that/does/not/exist.jpg"
    assert data["source_path"] == "/invalid/path/that/does/not/exist.jpg"
    assert data["layers_extracted"] == 0
    assert data["hardware_mode_used"] == "CPU"
    assert data["output_paths"] == []

def test_vectorize_file_not_found():
    response = client.post(
        "/vectorize",
        json={
            "source_path": "/invalid/path/that/does/not/exist.png",
            "output_path": "/tmp/AILayerEngine/output.svg"
        }
    )

    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "File not found: /invalid/path/that/does/not/exist.png"

@patch('main.get_hardware_mode', return_value="CPU")
def test_get_status(mock_get_hardware_mode):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "CPU"

def mock_to_thread(func, *args, **kwargs):
    import cv2
    if func == cv2.imread:
        return np.zeros((100, 100, 3), dtype=np.uint8)
    # Assume it's geometry_pipeline.process_layer
    return np.zeros((100, 100, 4), dtype=np.uint8)

@patch('main.get_hardware_mode', return_value="CPU")
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('asyncio.to_thread', side_effect=mock_to_thread)
@patch('main.inference_pipeline.run_rt_detr_detection', return_value=[(0, 0, 10, 10)])
@patch('main.inference_pipeline.preprocess_image_for_sam2', return_value=(None, (100, 100)))
@patch('main.inference_pipeline.run_sam2_segmentation', new_callable=AsyncMock, return_value=np.zeros((100, 100), dtype=np.uint8))
@patch('cv2.imwrite')
@patch('uuid.uuid4')
def test_extract_success(mock_uuid4, mock_imwrite, mock_sam2, mock_preprocess, mock_detection, mock_thread, mock_makedirs, mock_exists, mock_get_hardware_mode):
    class MockUUID:
        hex = "1234567890abcdef"
    mock_uuid4.return_value = MockUUID()

    response = client.post(
        "/extract",
        json={"source_path": "/dummy/path/dummy.jpg"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Extraction and Geometry Cleanup complete."
    assert data["layers_extracted"] == 1
    assert data["hardware_mode_used"] == "CPU"
    assert data["source_path"] == "/dummy/path/dummy.jpg"
    assert len(data["output_paths"]) == 1
    assert "layer_12345678_0.png" in data["output_paths"][0]

@patch('main.get_hardware_mode', return_value="CPU")
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('asyncio.to_thread', side_effect=mock_to_thread)
@patch('main.inference_pipeline.run_rt_detr_detection', return_value=[(0, 0, 10, 10)])
@patch('main.inference_pipeline.preprocess_image_for_sam2', return_value=(None, (100, 100)))
@patch('main.inference_pipeline.run_sam2_segmentation', new_callable=AsyncMock, side_effect=asyncio.TimeoutError())
@patch('main.inference_pipeline.run_rt_detr_fallback_mask', return_value=np.zeros((100, 100), dtype=np.uint8))
@patch('cv2.imwrite')
@patch('uuid.uuid4')
def test_extract_sam2_timeout_fallback(mock_uuid4, mock_imwrite, mock_fallback, mock_sam2, mock_preprocess, mock_detection, mock_thread, mock_makedirs, mock_exists, mock_get_hardware_mode):
    class MockUUID:
        hex = "1234567890abcdef"
    mock_uuid4.return_value = MockUUID()

    response = client.post(
        "/extract",
        json={"source_path": "/dummy/path/dummy.jpg"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["layers_extracted"] == 1
    mock_fallback.assert_called_once()

@patch('main.get_hardware_mode', return_value="CPU")
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('asyncio.to_thread', return_value=None)
def test_extract_decode_failure(mock_thread, mock_makedirs, mock_exists, mock_get_hardware_mode):
    response = client.post(
        "/extract",
        json={"source_path": "/dummy/path/dummy.jpg"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["layers_extracted"] == 0
    assert "Could not decode image at" in data["message"]

@patch('os.path.exists', return_value=True)
@patch('main.vectorization_pipeline.process_layer_to_svg', return_value="/tmp/AILayerEngine/output.svg")
def test_vectorize_success(mock_process, mock_exists):
    response = client.post(
        "/vectorize",
        json={
            "source_path": "/dummy/path/in.png",
            "output_path": "/tmp/AILayerEngine/output.svg"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["svg_path"] == "/tmp/AILayerEngine/output.svg"

@patch('os.path.exists', return_value=True)
@patch('main.vectorization_pipeline.process_layer_to_svg', side_effect=Exception("Test error"))
def test_vectorize_failure(mock_process, mock_exists):
    response = client.post(
        "/vectorize",
        json={
            "source_path": "/dummy/path/in.png",
            "output_path": "/tmp/AILayerEngine/output.svg"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["svg_path"] == ""

@patch('os.path.exists', return_value=True)
@patch('main.vectorization_pipeline.process_layer_to_svg', return_value="/tmp/AILayerEngine/output.svg")
def test_vectorize_path_traversal(mock_process, mock_exists):
    response = client.post(
        "/vectorize",
        json={
            "source_path": "/dummy/path/in.png",
            "output_path": "/tmp/AILayerEngine/../output.svg"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Verify the mocked function was called with the sanitized path
    mock_process.assert_called_once_with("/dummy/path/in.png", "/tmp/AILayerEngine/output.svg")
