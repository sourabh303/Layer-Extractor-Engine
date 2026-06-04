import asyncio
import time

async def process_task(i):
    await asyncio.sleep(0.5)  # Simulate some I/O or yielding task
    return i

async def original_sequential(bboxes):
    results = []
    for i, bbox in enumerate(bboxes):
        res = await process_task(i)
        results.append(res)
    return results

async def vectorized_concurrent(bboxes):
    tasks = []
    for i, bbox in enumerate(bboxes):
        tasks.append(process_task(i))
    results = await asyncio.gather(*tasks)
    return results

async def main():
    bboxes = list(range(10))

    start = time.perf_counter()
    res1 = await original_sequential(bboxes)
    orig_time = time.perf_counter() - start

    start = time.perf_counter()
    res2 = await vectorized_concurrent(bboxes)
    vec_time = time.perf_counter() - start

    print(f"Original: {orig_time:.4f}s")
    print(f"Concurrent: {vec_time:.4f}s")
    print(f"Speedup: {orig_time/vec_time:.2f}x")

asyncio.run(main())
