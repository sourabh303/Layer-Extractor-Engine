import cv2
import numpy as np
import time

def grabcut_original(img, bbox):
    h_orig, w_orig = img.shape[:2]
    mask = np.zeros((h_orig, w_orig), np.uint8)
    bgdModel = np.zeros((1,65), np.float64)
    fgdModel = np.zeros((1,65), np.float64)
    x1, y1, x2, y2 = bbox
    rect = (x1, y1, x2 - x1, y2 - y1)
    cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    return np.where((mask==2)|(mask==0), 0, 1).astype('uint8') * 255

def grabcut_optimized(img, bbox, margin=20):
    h_orig, w_orig = img.shape[:2]
    x1, y1, x2, y2 = bbox

    # Add margin
    cx1 = max(0, x1 - margin)
    cy1 = max(0, y1 - margin)
    cx2 = min(w_orig, x2 + margin)
    cy2 = min(h_orig, y2 + margin)

    crop_img = img[cy1:cy2, cx1:cx2]
    crop_mask = np.zeros(crop_img.shape[:2], np.uint8)

    bgdModel = np.zeros((1,65), np.float64)
    fgdModel = np.zeros((1,65), np.float64)

    # Adjust rect to cropped image
    rect = (x1 - cx1, y1 - cy1, x2 - x1, y2 - y1)

    cv2.grabCut(crop_img, crop_mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    crop_binary_mask = np.where((crop_mask==2)|(crop_mask==0), 0, 1).astype('uint8') * 255

    full_mask = np.zeros((h_orig, w_orig), np.uint8)
    full_mask[cy1:cy2, cx1:cx2] = crop_binary_mask
    return full_mask

img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
bbox = (500, 500, 600, 600)

start = time.perf_counter()
grabcut_original(img, bbox)
orig_time = time.perf_counter() - start

start = time.perf_counter()
grabcut_optimized(img, bbox)
opt_time = time.perf_counter() - start

print(f"Original: {orig_time:.4f}s")
print(f"Optimized: {opt_time:.4f}s")
print(f"Speedup: {orig_time/opt_time:.2f}x")
