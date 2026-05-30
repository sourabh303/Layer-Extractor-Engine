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

## 2024-05-24 - [OpenCV Spatial Array Optimization]
**Learning:** Performing NumPy masking (`cv2.inRange`) and contour extraction (`cv2.findContours`) across large full-resolution image arrays when the active mask covers only a small portion is highly inefficient. The time complexity scales with the image size ($O(W_{img} \times H_{img})$) rather than the feature size.
**Action:** When executing spatial OpenCV pipeline operations that operate within a mask, first compute the bounding box of the non-zero mask area (`cv2.boundingRect`), extract a localized Region of Interest (ROI), perform the heavy spatial operations on the ROI, and apply a coordinate offset when generating the final polygons to map back to the original image dimensions. This changes the complexity to $O(W_{box} \times H_{box})$.
