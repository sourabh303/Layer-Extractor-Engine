import os
import argparse
import asyncio
import uuid
import cv2
import uvicorn
import hmac
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from models.extraction_request import ExtractionRequest, ExtractionMetadataResponse
from utils.hardware import get_hardware_mode
from pipeline.inference import AIInferencePipeline
from pipeline.geometry import GeometryCleanupPipeline
from pipeline.vectorization import VectorizationPipeline

app = FastAPI(title="ML Service - AI Textile Layer Extraction")

# Initialize models
inference_pipeline = AIInferencePipeline()
geometry_pipeline = GeometryCleanupPipeline()
vectorization_pipeline = VectorizationPipeline()

@app.middleware("http")
async def verify_ipc_secret(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    secret = os.environ.get("IPC_SECRET")
    if not secret:
        # Fail securely if IPC_SECRET is not configured
        return JSONResponse(
            status_code=500,
            content={"detail": "IPC_SECRET environment variable is not set."}
        )

    provided_secret = request.headers.get("X-IPC-Secret", "")
    if not provided_secret:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized: Missing X-IPC-Secret header."}
        )

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided_secret.encode("utf-8"), secret.encode("utf-8")):
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized: Invalid IPC Secret."}
        )

    return await call_next(request)

class StatusResponse(BaseModel):
    mode: str

@app.get("/status", response_model=StatusResponse)
def get_status():
    """
    Returns the current hardware mode (GPU or CPU) for the UI to display
    the appropriate warning banner if needed.
    """
    mode = get_hardware_mode()
    return StatusResponse(mode=mode)

@app.post("/extract", response_model=ExtractionMetadataResponse)
async def run_extraction(request: ExtractionRequest):
    """
    Executes the full AI Extraction and Geometry Cleanup pipeline.
    Strictly accepts the absolute source_path to respect memory constraints
    and never transmits raw image bytes over HTTP.
    """
    source_path = request.source_path

    print(f"Received extraction request for: {source_path}")

    if not os.path.exists(source_path):
        return ExtractionMetadataResponse(
            status="error",
            message=f"File not found: {source_path}",
            source_path=source_path,
            layers_extracted=0,
            hardware_mode_used=get_hardware_mode(),
            output_paths=[]
        )

    # Create temp directory
    temp_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "AILayerEngine")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Load the source image using OpenCV
        # Ensure it's read in BGR format
        original_image = await asyncio.to_thread(cv2.imread, source_path)
        if original_image is None:
            raise ValueError(f"Could not decode image at {source_path}")

        # 1. Detection
        bboxes = inference_pipeline.run_rt_detr_detection(original_image)
        output_paths = []

        # Pre-process image for SAM2 once to save time
        preprocessed_tensor, original_shape = inference_pipeline.preprocess_image_for_sam2(original_image)

        # Process each detected motif
        for i, bbox in enumerate(bboxes):
            print(f"Processing bounding box {i+1}/{len(bboxes)}...")

            # 2. Segmentation (with Timeout Graceful Fallback)
            mask = None
            try:
                # 45 second timeout constraint
                mask = await asyncio.wait_for(
                    inference_pipeline.run_sam2_segmentation(preprocessed_tensor, original_shape, bbox),
                    timeout=45.0
                )
            except asyncio.TimeoutError:
                print("SAM2 segmentation timed out! Falling back to RT-DETR mask.")
                mask = inference_pipeline.run_rt_detr_fallback_mask(original_image, bbox)
            except Exception as e:
                print(f"SAM2 failed: {e}. Falling back to RT-DETR mask.")
                mask = inference_pipeline.run_rt_detr_fallback_mask(original_image, bbox)

            # 3. Geometry Cleanup (CRITICAL)
            # Run CPU-bound processing in a separate thread to unblock the async event loop
            flat_layer_rgba = await asyncio.to_thread(geometry_pipeline.process_layer, original_image, mask)

            # Save strictly flat geometry PNG output
            output_filename = f"layer_{uuid.uuid4().hex[:8]}_{i}.png"
            output_path = os.path.join(temp_dir, output_filename)
            cv2.imwrite(output_path, flat_layer_rgba)
            output_paths.append(output_path)

        return ExtractionMetadataResponse(
            status="success",
            message="Extraction and Geometry Cleanup complete.",
            source_path=source_path,
            layers_extracted=len(output_paths),
            hardware_mode_used=get_hardware_mode(),
            output_paths=output_paths
        )

    except Exception as e:
        print(f"Extraction failed: {e}")
        return ExtractionMetadataResponse(
            status="error",
            message=str(e),
            source_path=source_path,
            layers_extracted=0,
            hardware_mode_used=get_hardware_mode(),
            output_paths=[]
        )

class VectorizeRequest(BaseModel):
    source_path: str
    output_path: str

class VectorizeResponse(BaseModel):
    status: str
    svg_path: str

@app.post("/vectorize", response_model=VectorizeResponse)
def run_vectorization(request: VectorizeRequest):
    """
    Endpoint specifically to run the Raster-to-SVG vectorization step.
    Enforces strict polygon generation explicitly disabling curve fitting.
    """
    if not os.path.exists(request.source_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.source_path}")

    try:
        svg_path = vectorization_pipeline.process_layer_to_svg(
            request.source_path,
            request.output_path
        )
        return VectorizeResponse(status="success", svg_path=svg_path)
    except Exception as e:
        print(f"Vectorization failed: {e}")
        return VectorizeResponse(status="error", svg_path="")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the ML Service.")
    parser.add_argument("--port", type=int, required=True, help="Port to bind the service to.")
    args = parser.parse_args()

    # The Orchestrator assigns the port dynamically and passes it here.
    uvicorn.run(app, host="127.0.0.1", port=args.port)
