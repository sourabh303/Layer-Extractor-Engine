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
        masked_img = cv2.bitwise_and(image, image, mask=binary_mask)

        # 1. K-Means Quantization
        # Flatten image to 2D array of pixels for K-Means
        pixels = masked_img.reshape((-1, 3))
        pixels = np.float32(pixels)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, KMEANS_MAX_CLUSTERS, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        centers = np.uint8(centers)
        quantized_pixels = centers[labels.flatten()]
        quantized_img = quantized_pixels.reshape(masked_img.shape)

        # Re-apply mask as K-Means might have quantized the black background to something else
        quantized_img = cv2.bitwise_and(quantized_img, quantized_img, mask=binary_mask)

        # Create an empty RGBA output image (transparent background)
        h, w = image.shape[:2]
        flat_output = np.zeros((h, w, 4), dtype=np.uint8)

        # Process each quantized color cluster independently to generate flat polygons
        unique_colors = np.unique(quantized_img.reshape(-1, 3), axis=0)

        for color in unique_colors:
            # Skip the black background color
            if np.all(color == [0, 0, 0]):
                continue

            # Create a mask for this specific color
            color_mask = cv2.inRange(quantized_img, color, color)

            # Find contours for this color
            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
