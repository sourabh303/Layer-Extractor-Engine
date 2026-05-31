## 2024-05-27 - [Optimize K-Means Unique Color Extraction]
**Learning:** Extracting unique colors via `np.unique(quantized_img.reshape(-1, 3), axis=0)` on the full image array is extremely slow (O(H*W)). The exact same distinct colors are already available in the `centers` array returned by `cv2.kmeans` with maximum `K` length (e.g. 12).
**Action:** Always use the known cluster centers instead of scanning the full image array when trying to find unique colors after K-Means quantization.

## 2024-05-28 - [Avoid Running K-Means on Full Array if Only Foreground is Relevant]
**Learning:** Running `cv2.kmeans` on an entire flattened image (`image.reshape((-1, 3))`) after applying a mask (where the background is black) wastes immense CPU time evaluating the massive cluster of background pixels.
**Action:** When clustering colors inside a specific foreground area, extract the pixels explicitly (`pixels = image[binary_mask > 0]`) and run K-Means *only* on that subset. Then reconstruct the image. This can yield ~40x speedups (O(W*H) -> O(N_foreground)).

## 2025-05-29 - [Optimize SkiaSharp Pixel Extraction in C#]
**Learning:** Calling `SKBitmap.GetPixel(x, y)` inside a nested loop for an entire image (O(W*H)) in SkiaSharp introduces massive method call overhead, causing significant performance degradation during large operations like PSD export.
**Action:** When extracting full-image pixel channels in C#, use `unsafe` byte pointers (`(byte*)bitmap.GetPixels().ToPointer()`) directly for known fast formats (e.g. `Bgra8888` or `Rgba8888`), or fall back to `bitmap.Pixels` (a `ReadOnlySpan<SKColor>`). This drastically reduces the overhead per pixel.

## 2025-05-29 - [Check Stride/RowBytes in unsafe SkiaSharp pixel blocks]
**Learning:** Assuming that an image buffer's `layer.Bitmap.GetPixels()` perfectly fits `width * 4` per row is dangerous. If there is padding (stride > width * 4), reading continuously as `ptr[i * 4]` will cross row boundaries incorrectly and corrupt the image.
**Action:** Always check that `layer.Bitmap.RowBytes == width * 4` before attempting a fast continuous 1D-array style unsafe pixel read, or manually step through rows via a `y` loop using `byte* rowPtr = ptr + (y * layer.Bitmap.RowBytes)`.

## 2025-05-31 - [Optimize OpenCV Spatial Operations via Bounding Box Cropping]
**Learning:** Running spatial operations like `cv2.inRange` and `cv2.findContours` on a full high-resolution image array where the actual motif occupies only a small fraction wastes significant computation.
**Action:** When performing OpenCV spatial processing on masked areas, extract the bounding box using `cv2.boundingRect(mask)`, crop the image to those dimensions before running the spatial operations, and pass the `offset=(x, y)` parameter to `cv2.findContours` to map coordinates back to the original image space. This changes processing time from O(W*H) to O(bbox_W*bbox_H).

## 2026-05-31
**Title:** Optimizing OpenCV Spatial Cropping Avoidance of Double Shift
**Learning:** When passing `offset=(x, y)` to `cv2.findContours` on a sub-cropped array (obtained via `cv2.boundingRect`), the resulting coordinates are already shifted to the global image space. Manually adding `[x, y]` to the contours later causes a double-shift bug. Furthermore, do not re-crop arrays that are already scaled to the ROI.
**Action:** Fixed `ml-service/pipeline/geometry.py` to prevent slicing a previously-cropped image and removed the double-shift coordinate logic in the contour extraction pipeline.

## Date: 2026-05-31
### Title: Remove Redundant Image I/O in ML Inference Pipeline
**Learning:** In the ML pipeline (`inference.py` and `main.py`), passing a file path string and independently loading the image from disk via `cv2.imread` inside each bounding box processing loop (and inside async threads) caused massive I/O overhead. This is especially severe since `main.py` had already loaded the original image.
**Action:** Refactored `run_rt_detr_detection`, `run_sam2_segmentation`, and `run_rt_detr_fallback_mask` to accept an already loaded `np.ndarray` image matrix (`original_img`) instead of a file path. Reduced processing time significantly for large batches/images (e.g., from ~15s down to ~7s for 50 iterations on a 4K image). When extracting dimensions from the numpy array for `MOCK_INFERENCE`, properly used `h, w = original_img.shape[:2]` to account for the difference between Pillow and OpenCV format.
