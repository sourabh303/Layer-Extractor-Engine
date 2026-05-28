## 2024-05-27 - [Optimize K-Means Unique Color Extraction]
**Learning:** Extracting unique colors via `np.unique(quantized_img.reshape(-1, 3), axis=0)` on the full image array is extremely slow (O(H*W)). The exact same distinct colors are already available in the `centers` array returned by `cv2.kmeans` with maximum `K` length (e.g. 12).
**Action:** Always use the known cluster centers instead of scanning the full image array when trying to find unique colors after K-Means quantization.

## 2024-05-28 - [Avoid Running K-Means on Full Array if Only Foreground is Relevant]
**Learning:** Running `cv2.kmeans` on an entire flattened image (`image.reshape((-1, 3))`) after applying a mask (where the background is black) wastes immense CPU time evaluating the massive cluster of background pixels.
**Action:** When clustering colors inside a specific foreground area, extract the pixels explicitly (`pixels = image[binary_mask > 0]`) and run K-Means *only* on that subset. Then reconstruct the image. This can yield ~40x speedups (O(W*H) -> O(N_foreground)).
