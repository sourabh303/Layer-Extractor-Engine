import cv2
import numpy as np
import time

def grabcut_full(original_img, bbox):
    h_orig, w_orig = original_img.shape[:2]
    mask = np.zeros((h_orig, w_orig), np.uint8)
    bgdModel = np.zeros((1,65), np.float64)
    fgdModel = np.zeros((1,65), np.float64)
    x1, y1, x2, y2 = bbox
    rect = (x1, y1, x2 - x1, y2 - y1)

    start = time.perf_counter()
    cv2.grabCut(original_img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    binary_mask = np.where((mask==2)|(mask==0), 0, 1).astype('uint8') * 255
    return time.perf_counter() - start, binary_mask

def grabcut_cropped(original_img, bbox):
    h_orig, w_orig = original_img.shape[:2]
    x1, y1, x2, y2 = bbox

    margin = 50
    x1_crop = max(0, x1 - margin)
    y1_crop = max(0, y1 - margin)
    x2_crop = min(w_orig, x2 + margin)
    y2_crop = min(h_orig, y2 + margin)

    cropped_img = original_img[y1_crop:y2_crop, x1_crop:x2_crop]
    cropped_mask = np.zeros(cropped_img.shape[:2], np.uint8)
    bgdModel = np.zeros((1,65), np.float64)
    fgdModel = np.zeros((1,65), np.float64)

    rect_cropped = (x1 - x1_crop, y1 - y1_crop, x2 - x1, y2 - y1)

    start = time.perf_counter()
    cv2.grabCut(cropped_img, cropped_mask, rect_cropped, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    cropped_binary = np.where((cropped_mask==2)|(cropped_mask==0), 0, 1).astype('uint8') * 255

    binary_mask = np.zeros((h_orig, w_orig), dtype='uint8')
    binary_mask[y1_crop:y2_crop, x1_crop:x2_crop] = cropped_binary
    return time.perf_counter() - start, binary_mask

img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
bbox = (500, 400, 700, 600) # 200x200 object

t1, _ = grabcut_full(img, bbox)
t2, _ = grabcut_cropped(img, bbox)

print(f"Full: {t1:.4f}s")
print(f"Cropped: {t2:.4f}s")
print(f"Speedup: {t1/t2:.2f}x")
