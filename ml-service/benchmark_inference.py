import numpy as np
import time

def original_method(predictions, w_orig, h_orig):
    bboxes = []
    conf_threshold = 0.5
    for pred in predictions:
        if len(pred) >= 6:
            x_c, y_c, w, h_box, conf = pred[0:5]
            score = conf if conf <= 1.0 else np.max(pred[5:])
            if score > conf_threshold:
                x1 = int((x_c - w/2) * w_orig)
                y1 = int((y_c - h_box/2) * h_orig)
                x2 = int((x_c + w/2) * w_orig)
                y2 = int((y_c + h_box/2) * h_orig)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w_orig, x2), min(h_orig, y2)
                bboxes.append((x1, y1, x2, y2))
    return bboxes

def vectorized_method(predictions, w_orig, h_orig):
    conf_threshold = 0.5

    if len(predictions.shape) != 2 or predictions.shape[1] < 6:
        # If it's a list of 1D arrays or irregular, it's safer to check
        # But assuming outputs[0][0] from ONNX is a 2D numpy array
        return []

    confs = predictions[:, 4]
    class_max = np.max(predictions[:, 5:], axis=1)
    scores = np.where(confs <= 1.0, confs, class_max)

    mask = scores > conf_threshold
    valid_preds = predictions[mask]

    if len(valid_preds) == 0:
        return []

    x_c, y_c, w, h_box = valid_preds[:, 0], valid_preds[:, 1], valid_preds[:, 2], valid_preds[:, 3]

    x1 = (x_c - w / 2) * w_orig
    y1 = (y_c - h_box / 2) * h_orig
    x2 = (x_c + w / 2) * w_orig
    y2 = (y_c + h_box / 2) * h_orig

    x1 = np.clip(x1, 0, None).astype(int)
    y1 = np.clip(y1, 0, None).astype(int)
    x2 = np.clip(x2, None, w_orig).astype(int)
    y2 = np.clip(y2, None, h_orig).astype(int)

    # zip converts parallel numpy arrays into list of tuples very fast
    return list(zip(x1.tolist(), y1.tolist(), x2.tolist(), y2.tolist()))

N = 10000
np.random.seed(42)
predictions = np.random.rand(N, 85)
predictions[:, 4] = np.random.uniform(0.0, 1.5, N)

w_orig = 1920
h_orig = 1080

start = time.perf_counter()
for _ in range(100):
    res1 = original_method(predictions, w_orig, h_orig)
orig_time = time.perf_counter() - start

start = time.perf_counter()
for _ in range(100):
    res2 = vectorized_method(predictions, w_orig, h_orig)
vec_time = time.perf_counter() - start

print(f"Original: {orig_time:.4f}s")
print(f"Vectorized: {vec_time:.4f}s")
print(f"Speedup: {orig_time/vec_time:.2f}x")
print(f"Match: {res1 == res2}")
