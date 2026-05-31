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

        # Extract the ROI specified by the mask
        # ⚡ Bolt Optimization: Only extract and process pixels that are strictly in the foreground
        # This reduces K-Means time from O(W*H) to O(N) where N is number of foreground pixels
        fg_mask = binary_mask > 0
        pixels = image[fg_mask]

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

        # Reconstruct full image size with quantized pixels inside the mask
        quantized_img = np.zeros_like(image)
        quantized_img[fg_mask] = centers[labels.flatten()]

        # Create an empty RGBA output image (transparent background)
        h, w = image.shape[:2]
        flat_output = np.zeros((h, w, 4), dtype=np.uint8)

        # Process each quantized color cluster independently to generate flat polygons
        unique_colors = np.unique(centers, axis=0)

        # ⚡ Bolt Optimization: Crop spatial operations to the bounding box of the foreground
        # This reduces findContours and inRange time from O(W*H) to O(bbox_W * bbox_H)
        x, y, w_box, h_box = cv2.boundingRect(binary_mask)
        cropped_quantized_img = quantized_img[y:y+h_box, x:x+w_box]

        for color in unique_colors:
            # Skip the black background color
            if np.all(color == [0, 0, 0]):
                continue

            # Create a mask for this specific color on the cropped image
            color_mask = cv2.inRange(cropped_quantized_img, color, color)

            # Find contours for this color using the offset to map back to original coordinates
            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE, offset=(x, y))

            # 2. Geometry Cleanup: approxPolyDP
            flat_polygons = []
            for contour in contours:
                epsilon = APPROX_POLY_DP_EPSILON_MULTIPLIER * cv2.arcLength(contour, True)
                approx_polygon = cv2.approxPolyDP(contour, epsilon, True)
                flat_polygons.append(approx_polygon)

            # 3. Reconstruct by filling the strictly flat polygons
            # Color is BGR from OpenCV, add alpha channel 255
            rgba_color = (int(color[0]), int(color[1]), int(color[2]), 255)
            cv2.fillPoly(flat_output, flat_polygons, rgba_color)

        return flat_output
