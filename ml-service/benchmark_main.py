import asyncio
import time
import numpy as np
import uuid
import os

from pipeline.inference import AIInferencePipeline
from pipeline.geometry import GeometryCleanupPipeline
import cv2

os.environ["MOCK_INFERENCE"] = "true"

inference_pipeline = AIInferencePipeline()

async def old_approach(original_image):
    bboxes = inference_pipeline.run_rt_detr_detection(original_image)
    preprocessed_tensor, original_shape = inference_pipeline.preprocess_image_for_sam2(original_image)
    return bboxes, preprocessed_tensor, original_shape

async def new_approach(original_image):
    bboxes = await asyncio.to_thread(inference_pipeline.run_rt_detr_detection, original_image)
    preprocessed_tensor, original_shape = await asyncio.to_thread(inference_pipeline.preprocess_image_for_sam2, original_image)
    return bboxes, preprocessed_tensor, original_shape

async def main():
    h, w = 1080, 1920
    original_image = np.zeros((h, w, 3), dtype=np.uint8)

    # Warmup
    await old_approach(original_image)
    await new_approach(original_image)

    num_iterations = 100

    start = time.perf_counter()
    for _ in range(num_iterations):
        await old_approach(original_image)
    old_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(num_iterations):
        await new_approach(original_image)
    new_time = time.perf_counter() - start

    print(f"Old Approach (Blocking Event Loop): {old_time:.4f}s")
    print(f"New Approach (asyncio.to_thread): {new_time:.4f}s")

    # We are testing blocking nature, not absolute time difference on mock.
    print(f"Performance impact: It prevents the event loop from being blocked for long CPU-bound operations in the pipeline.")

asyncio.run(main())
