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
        x, y, w_box, h_box = cv2.boundingRect(binary_mask)
        if w_box == 0 or h_box == 0:
            h, w = image.shape[:2]
            return np.zeros((h, w, 4), dtype=np.uint8)

        roi_image = image[y:y+h_box, x:x+w_box]
        roi_mask = binary_mask[y:y+h_box, x:x+w_box]

        fg_mask = roi_mask > 0
        pixels = roi_image[fg_mask]

        if len(pixels) == 0:
            h, w = image.shape[:2]
            return np.zeros((h, w, 4), dtype=np.uint8)

        pixels = np.float32(pixels)

        k = min(KMEANS_MAX_CLUSTERS, len(pixels))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        centers = np.uint8(centers)

        h_orig, w_orig = image.shape[:2]
        flat_output = np.zeros((h_orig, w_orig, 4), dtype=np.uint8)

        # Create localized 2D label array
        labels_flat = labels.flatten()
        label_img = np.full((h_box, w_box), -1, dtype=np.int32)
        label_img[fg_mask] = labels_flat

        for i, color in enumerate(centers):
            if color[0] == 0 and color[1] == 0 and color[2] == 0:
                continue

            # Vectorized boolean indexing is typically faster than inRange on an RGB image
            color_mask = np.where(label_img == i, 255, 0).astype(np.uint8)

            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE, offset=(x, y))

            flat_polygons = []
            for contour in contours:
                epsilon = APPROX_POLY_DP_EPSILON_MULTIPLIER * cv2.arcLength(contour, True)
                approx_polygon = cv2.approxPolyDP(contour, epsilon, True)
                flat_polygons.append(approx_polygon)

            rgba_color = (int(color[0]), int(color[1]), int(color[2]), 255)
            cv2.fillPoly(flat_output, flat_polygons, rgba_color)

        return flat_output
