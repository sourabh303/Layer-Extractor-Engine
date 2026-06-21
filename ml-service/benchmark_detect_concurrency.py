import asyncio
import time
import numpy as np
import uvicorn
import multiprocessing
import httpx

from main import app
import os
import cv2

os.environ["IPC_SECRET"] = "testsecret"
os.environ["MOCK_INFERENCE"] = "false"

# Create a slow inference pipeline mock
from pipeline.inference import AIInferencePipeline
original_run_rt_detr_detection = AIInferencePipeline.run_rt_detr_detection

def slow_run_rt_detr_detection(self, img):
    time.sleep(1.0)
    return original_run_rt_detr_detection(self, img)

AIInferencePipeline.run_rt_detr_detection = slow_run_rt_detr_detection
AIInferencePipeline.preprocess_image_for_sam2 = lambda self, img: (None, (100, 100))
AIInferencePipeline.run_sam2_segmentation = lambda self, pt, os, bb, oi: np.zeros((100,100), dtype=np.uint8)


def run_server():
    import unittest.mock
    with unittest.mock.patch.object(AIInferencePipeline, '_load_models'):
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

async def make_request(client, data):
    return await client.post("http://127.0.0.1:8000/extract", json=data, headers={"X-IPC-Secret": "testsecret"}, timeout=60.0)

async def main():
    p = multiprocessing.Process(target=run_server)
    p.start()
    time.sleep(2)  # wait for server to start

    # Create dummy image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite("/tmp/test_img.png", img)

    data = {"source_path": "/tmp/test_img.png"}

    async with httpx.AsyncClient() as client:
        print("Benchmarking concurrent requests...")
        start = time.perf_counter()

        # send 5 requests concurrently
        tasks = [make_request(client, data) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        end = time.perf_counter()
        print(f"Total time for 5 requests: {end - start:.4f} seconds")

        # check status
        for r in results:
            if r.status_code != 200:
                print(r.text)

    p.terminate()
    p.join()

asyncio.run(main())
