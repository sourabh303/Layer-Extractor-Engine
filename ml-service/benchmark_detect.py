import asyncio
import time
import numpy as np

class MockInferencePipeline:
    def __init__(self):
        pass

    def run_rt_detr_detection(self, original_img):
        # Simulate blocking work
        time.sleep(1)
        return [(0,0,10,10), (10,10,20,20)]

async def test_main():
    inference_pipeline = MockInferencePipeline()
    original_image = np.zeros((100,100,3), dtype=np.uint8)

    print("Benchmarking sequential detection...")
    start = time.perf_counter()
    bboxes1 = inference_pipeline.run_rt_detr_detection(original_image)
    end = time.perf_counter()
    seq_time = end - start
    print(f"Sequential detection took {seq_time:.4f} seconds")

    print("Benchmarking async detection with to_thread...")
    start = time.perf_counter()
    bboxes2 = await asyncio.to_thread(inference_pipeline.run_rt_detr_detection, original_image)
    end = time.perf_counter()
    async_time = end - start
    print(f"Async detection took {async_time:.4f} seconds")

    print(f"Both returned same boxes: {bboxes1 == bboxes2}")

asyncio.run(test_main())
