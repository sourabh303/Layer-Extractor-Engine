import sys
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

# Add the ml-service directory to the python path so we can import from main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

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
            "output_path": "/tmp/output.svg"
        }
    )

    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "File not found: /invalid/path/that/does/not/exist.png"
