import argparse
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from models.extraction_request import ExtractionRequest
from utils.hardware import get_hardware_mode

app = FastAPI(title="ML Service - AI Textile Layer Extraction")

class StatusResponse(BaseModel):
    mode: str

class ExtractionMetadataResponse(BaseModel):
    status: str
    message: str
    source_path: str
    layers_extracted: int
    hardware_mode_used: str

@app.get("/status", response_model=StatusResponse)
def get_status():
    """
    Returns the current hardware mode (GPU or CPU) for the UI to display
    the appropriate warning banner if needed.
    """
    mode = get_hardware_mode()
    return StatusResponse(mode=mode)

@app.post("/extract", response_model=ExtractionMetadataResponse)
def run_extraction(request: ExtractionRequest):
    """
    Mock endpoint for image extraction.
    Strictly accepts the absolute source_path to respect memory constraints
    and never transmits raw image bytes over HTTP.
    """
    source_path = request.source_path

    print(f"Received extraction request for: {source_path}")

    # Return mock metadata
    return ExtractionMetadataResponse(
        status="success",
        message="Mock extraction complete.",
        source_path=source_path,
        layers_extracted=4,
        hardware_mode_used=get_hardware_mode()
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the ML Service.")
    parser.add_argument("--port", type=int, required=True, help="Port to bind the service to.")
    args = parser.parse_args()

    # The Orchestrator assigns the port dynamically and passes it here.
    uvicorn.run(app, host="127.0.0.1", port=args.port)
