import cv2
import numpy as np

from config.geometry import KMEANS_MAX_CLUSTERS, APPROX_POLY_DP_EPSILON_MULTIPLIER

class GeometryCleanupPipeline:
    @staticmethod
    def process_layer(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Processes a single extracted layer (image + mask) enforcing strictly flat geometry.
        1. Applies K-Means quantization to eliminate gradient variance.
        2. Applies approxPolyDP to eliminate fabric curves and folds.
        3. Reconstructs the image onto a transparent background using ONLY the flat polygons.
        """
        # Ensure mask is binary
        _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

        # Extract bounding box to crop spatial processing
        # ⚡ Bolt Optimization: By processing only the bounding box instead of the full image
        # we reduce spatial operations (masking, inRange, findContours) from O(W_img*H_img) to O(W_box*H_box)
        x, y, w_box, h_box = cv2.boundingRect(binary_mask)
        if w_box == 0 or h_box == 0:
            h, w = image.shape[:2]
            return np.zeros((h, w, 4), dtype=np.uint8)

        roi_image = image[y:y+h_box, x:x+w_box]
        roi_mask = binary_mask[y:y+h_box, x:x+w_box]

        # Extract the ROI specified by the mask
        # ⚡ Bolt Optimization: Only extract and process pixels that are strictly in the foreground
        # This reduces K-Means time from O(W*H) to O(N) where N is number of foreground pixels
        fg_mask = roi_mask > 0
        pixels = roi_image[fg_mask]

        # If the mask is empty, return an empty image early
        if len(pixels) == 0:
            h, w = image.shape[:2]
            return np.zeros((h, w, 4), dtype=np.uint8)

        # 1. K-Means Quantization
        pixels = np.float32(pixels)

        # Handle edge case where number of foreground pixels is less than K
        k = min(KMEANS_MAX_CLUSTERS, len(pixels))

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        centers = np.uint8(centers)

        # Reconstruct localized image size with quantized labels inside the mask
        # ⚡ Bolt Optimization: Map K-Means labels directly to an integer array instead of reconstructing
        # the RGB image and using cv2.inRange. This allows fast O(N) boolean indexing per cluster,
        # avoiding redundant O(W*H) pixel comparisons across all channels for every color.
        label_img = np.zeros(roi_image.shape[:2], dtype=np.int32) - 1 # -1 is background
        label_img[fg_mask] = labels.flatten()

        # Create an empty RGBA output image (transparent background) with ORIGINAL image dimensions
        h_orig, w_orig = image.shape[:2]
        flat_output = np.zeros((h_orig, w_orig, 4), dtype=np.uint8)

        # Process each quantized color cluster independently to generate flat polygons
        unique_labels = np.unique(labels)

        # Note: label_img is ALREADY cropped to the bounding box (roi_image size).
        # We simply use the already-cropped image directly.

        for i in unique_labels:
            color = centers[i]
            # Skip the black background color
            if np.all(color == [0, 0, 0]):
                continue

            # Create a mask for this specific label using fast boolean indexing
            # We use np.ascontiguousarray to ensure memory layout compatibility with findContours
            color_mask = (label_img == i).astype(np.uint8) * 255
            color_mask = np.ascontiguousarray(color_mask)

            # Find contours for this color using the offset to map back to original coordinates
            # Note: We ONLY apply the offset in findContours or here, not both!
            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE, offset=(x, y))

            # 2. Geometry Cleanup: approxPolyDP
            flat_polygons = []
            for contour in contours:
                epsilon = APPROX_POLY_DP_EPSILON_MULTIPLIER * cv2.arcLength(contour, True)
                approx_polygon = cv2.approxPolyDP(contour, epsilon, True)
                # The findContours offset argument already shifts the coordinates,
                # so we do not add [x, y] again to prevent a double-shift bug.
                flat_polygons.append(approx_polygon)

            # 3. Reconstruct by filling the strictly flat polygons
            # Color is BGR from OpenCV, add alpha channel 255
            rgba_color = (int(color[0]), int(color[1]), int(color[2]), 255)
            cv2.fillPoly(flat_output, flat_polygons, rgba_color)

        return flat_output
