import asyncio
import time
import numpy as np
import uuid
import os

from pipeline.inference import AIInferencePipeline
from pipeline.geometry import GeometryCleanupPipeline

import os
os.environ["MOCK_INFERENCE"] = "true"
# Mock pipelines
inference_pipeline = AIInferencePipeline()
geometry_pipeline = GeometryCleanupPipeline()

async def process_bbox_sequential(bboxes, preprocessed_tensor, original_shape, original_image, temp_dir):
    output_paths = []
    for i, bbox in enumerate(bboxes):
        try:
            mask = await asyncio.wait_for(
                inference_pipeline.run_sam2_segmentation(preprocessed_tensor, original_shape, bbox),
                timeout=45.0
            )
        except Exception as e:
            mask = inference_pipeline.run_rt_detr_fallback_mask(original_image, bbox)

        flat_layer_rgba = await asyncio.to_thread(geometry_pipeline.process_layer, original_image, mask)

        output_filename = f"layer_{uuid.uuid4().hex[:8]}_{i}.png"
        output_path = os.path.join(temp_dir, output_filename)
        output_paths.append(output_path)
    return output_paths

async def process_bbox_concurrent(bboxes, preprocessed_tensor, original_shape, original_image, temp_dir):
    async def process_single_bbox(i, bbox):
        try:
            mask = await asyncio.wait_for(
                inference_pipeline.run_sam2_segmentation(preprocessed_tensor, original_shape, bbox),
                timeout=45.0
            )
        except Exception as e:
            mask = inference_pipeline.run_rt_detr_fallback_mask(original_image, bbox)

        flat_layer_rgba = await asyncio.to_thread(geometry_pipeline.process_layer, original_image, mask)

        output_filename = f"layer_{uuid.uuid4().hex[:8]}_{i}.png"
        output_path = os.path.join(temp_dir, output_filename)
        return output_path

    tasks = [process_single_bbox(i, bbox) for i, bbox in enumerate(bboxes)]
    return await asyncio.gather(*tasks)

async def main():
    # Setup dummy data
    h, w = 1080, 1920
    original_image = np.zeros((h, w, 3), dtype=np.uint8)
    bboxes = [
        (int(w*0.1), int(h*0.1), int(w*0.4), int(h*0.4)),
        (int(w*0.5), int(h*0.5), int(w*0.9), int(h*0.9)),
        (int(w*0.2), int(h*0.2), int(w*0.3), int(h*0.3)),
        (int(w*0.6), int(h*0.6), int(w*0.8), int(h*0.8))
    ]
    preprocessed_tensor, original_shape = inference_pipeline.preprocess_image_for_sam2(original_image)
    temp_dir = "/tmp/AILayerEngineBench"
    os.makedirs(temp_dir, exist_ok=True)
    os.chmod(temp_dir, 0o700)

    # Warmup
    await process_bbox_sequential(bboxes[:1], preprocessed_tensor, original_shape, original_image, temp_dir)

    start = time.perf_counter()
    await process_bbox_sequential(bboxes, preprocessed_tensor, original_shape, original_image, temp_dir)
    seq_time = time.perf_counter() - start

    start = time.perf_counter()
    await process_bbox_concurrent(bboxes, preprocessed_tensor, original_shape, original_image, temp_dir)
    conc_time = time.perf_counter() - start

    print(f"Sequential: {seq_time:.4f}s")
    print(f"Concurrent: {conc_time:.4f}s")
    print(f"Speedup: {seq_time/conc_time:.2f}x")

asyncio.run(main())
