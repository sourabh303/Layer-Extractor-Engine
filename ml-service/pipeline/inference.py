import os
import asyncio
import numpy as np

# Determines if we should bypass loading actual weights for the local sandbox
MOCK_INFERENCE = os.getenv("MOCK_INFERENCE", "false").lower() == "true"

class AIInferencePipeline:
    def __init__(self):
        self.rt_detr_session = None
        self.sam2_model = None

        if not MOCK_INFERENCE:
            self._load_models()

    def _load_models(self):
        """
        Loads the actual ONNX RT-DETR and PyTorch SAM2 models.
        In the Phase 2 GitHub action / Sandbox, this is skipped to avoid downloading massive weights.
        """
        import onnxruntime as ort
        import torch
        from utils.hardware import get_execution_providers

        print("Loading real RT-DETR and SAM2 models...")

        # Load RT-DETR ONNX Model
        model_path = os.path.join(os.getcwd(), "models", "rt_detr.onnx")
        if os.path.exists(model_path):
            self.rt_detr_session = ort.InferenceSession(model_path, providers=get_execution_providers())
        else:
            print(f"WARNING: RT-DETR model not found at {model_path}. Inference will fail if not mocked.")

        # Load SAM2 PyTorch Model
        sam2_path = os.path.join(os.getcwd(), "models", "sam2.pt")
        if os.path.exists(sam2_path):
            # Select device based on PyTorch CUDA availability
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

            # Load SAM2 model (typically via custom architecture wrapper or torch.jit)
            # Assuming a standard torchscript model or similar loaded directly for inference
            try:
                self.sam2_model = torch.jit.load(sam2_path).to(device)
                self.sam2_model.eval()
            except Exception as e:
                print(f"Failed to load SAM2 model as torchscript: {e}. If it's a state_dict, you need the architecture definitions.")
                # We do a basic torch.load as a placeholder, real integration depends on the SAM2 repo structure
                self.sam2_model = torch.load(sam2_path, map_location=device)
        else:
            print(f"WARNING: SAM2 model not found at {sam2_path}. Inference will fail if not mocked.")

    def run_rt_detr_detection(self, original_img: np.ndarray) -> list[tuple]:
        """
        Runs RT-DETR to detect motifs and returns a list of bounding boxes.
        Returns: [(x1, y1, x2, y2), ...]
        """
        import cv2

        if MOCK_INFERENCE:
            gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
            kernel = np.ones((3,3), np.uint8)
            opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            bboxes = []
            for c in contours:
                x, y, w, h_box = cv2.boundingRect(c)
                if w >= 15 and h_box >= 15:
                    bboxes.append((int(x), int(y), int(x+w), int(y+h_box)))
            return bboxes


        if not self.rt_detr_session:
            raise RuntimeError("RT-DETR session not loaded.")

        # 1. Preprocess Image
        # Assuming typical RT-DETR preprocessing: resize to 640x640, normalize, CHW format
        if original_img is None:
            raise ValueError("Provided image array is None.")

        h_orig, w_orig = original_img.shape[:2]
        img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (640, 640))
        img = img.astype(np.float32) / 255.0

        # Typically RT-DETR expects standard ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img = (img - mean) / std

        img = img.transpose((2, 0, 1)) # HWC to CHW
        input_tensor = np.expand_dims(img, axis=0) # Add batch dimension -> BCHW

        # 2. Run Inference
        # ONNX sessions typically require dictionary mapping input names to numpy arrays
        input_name = self.rt_detr_session.get_inputs()[0].name
        outputs = self.rt_detr_session.run(None, {input_name: input_tensor})

        # 3. Postprocess
        # Assuming output[0] is boxes [B, N, 4] and output[1] is scores [B, N, num_classes]
        # Or a combined output [B, N, 6] (x1, y1, x2, y2, score, class)
        # Using a generic post-processing assumption for standard YOLO/RT-DETR formats
        predictions = outputs[0][0] # Get first batch element

        conf_threshold = 0.5

        if len(predictions.shape) != 2 or predictions.shape[1] < 6:
            return []

        confs = predictions[:, 4]
        class_max = np.max(predictions[:, 5:], axis=1)
        scores = np.where(confs <= 1.0, confs, class_max)

        mask = scores > conf_threshold
        valid_preds = predictions[mask]

        if len(valid_preds) == 0:
            return []

        x_c = valid_preds[:, 0]
        y_c = valid_preds[:, 1]
        w = valid_preds[:, 2]
        h_box = valid_preds[:, 3]

        x1 = (x_c - w / 2) * w_orig
        y1 = (y_c - h_box / 2) * h_orig
        x2 = (x_c + w / 2) * w_orig
        y2 = (y_c + h_box / 2) * h_orig

        x1 = np.clip(x1, 0, None).astype(int)
        y1 = np.clip(y1, 0, None).astype(int)
        x2 = np.clip(x2, None, w_orig).astype(int)
        y2 = np.clip(y2, None, h_orig).astype(int)

        bboxes = list(zip(x1.tolist(), y1.tolist(), x2.tolist(), y2.tolist()))

        return bboxes

    def preprocess_image_for_sam2(self, original_img: np.ndarray) -> tuple:
        """
        Preprocesses the original image once for SAM2 inference.
        Returns a tuple of (preprocessed_tensor, original_shape).
        """
        if MOCK_INFERENCE:
            # Return dummy tensor and original shape for mock
            h_orig, w_orig = original_img.shape[:2]
            return None, (h_orig, w_orig)

        import torch
        import cv2

        if not self.sam2_model:
            raise RuntimeError("SAM2 model not loaded.")

        img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        h_orig, w_orig = img.shape[:2]

        device = next(self.sam2_model.parameters()).device

        input_image = cv2.resize(img, (1024, 1024))
        input_tensor = torch.as_tensor(input_image, device=device).permute(2, 0, 1).unsqueeze(0).float()

        return input_tensor, (h_orig, w_orig)

    async def run_sam2_segmentation(self, preprocessed_tensor, original_shape: tuple, bbox: tuple, original_img: np.ndarray = None) -> np.ndarray:
        """
        Runs SAM2 inference asynchronously to generate a high-quality segmentation mask.
        Returns a binary numpy array (mask).
        """
        import cv2
        import numpy as np

        if MOCK_INFERENCE:
            # Simulate processing time
            await asyncio.sleep(0.1)

            h, w = original_shape
            mask = np.zeros((h, w), dtype=np.uint8)

            if original_img is not None:
                gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
                kernel = np.ones((3,3), np.uint8)
                opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
                closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=2)
                contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # Find the contour that matches this bbox
                target_bbox = bbox
                for c in contours:
                    bx, by, bw, bh = cv2.boundingRect(c)
                    c_bbox = (bx, by, bx+bw, by+bh)
                    if c_bbox == target_bbox:
                        cv2.drawContours(mask, [c], -1, 255, thickness=cv2.FILLED)
                        break
            else:
                x1, y1, x2, y2 = bbox
                mask[y1:y2, x1:x2] = 255

            return mask

        import torch


        if not self.sam2_model:
            raise RuntimeError("SAM2 model not loaded.")

        # Run inside an executor since PyTorch inference is blocking CPU/GPU bound
        loop = asyncio.get_running_loop()

        def _sync_sam2_inference():
            h_orig, w_orig = original_shape
            device = next(self.sam2_model.parameters()).device

            # Normalize bounding box for the 1024x1024 scale
            x1, y1, x2, y2 = bbox
            scale_x = 1024 / w_orig
            scale_y = 1024 / h_orig
            box_1024 = torch.tensor([[x1*scale_x, y1*scale_y, x2*scale_x, y2*scale_y]], device=device)

            with torch.no_grad():
                # Forward pass: getting image embeddings and decoding masks
                # (Actual SAM2 API uses build_sam2_predictor and predictor.set_image(), predictor.predict())
                # Here we pass the tensor and box directly to the loaded model representation
                masks, scores, _ = self.sam2_model(preprocessed_tensor, boxes=box_1024)

            # Select the mask with the highest score
            best_mask_idx = torch.argmax(scores).item()
            best_mask = masks[0, best_mask_idx].cpu().numpy()

            # Resize the mask back to the original image dimensions
            best_mask_resized = cv2.resize(best_mask, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)

            # Threshold to create binary mask (0 or 255)
            binary_mask = (best_mask_resized > 0.0).astype(np.uint8) * 255

            return binary_mask

        # Execute the blocking inference in a separate thread
        mask = await loop.run_in_executor(None, _sync_sam2_inference)
        return mask

    def run_rt_detr_fallback_mask(self, original_img: np.ndarray, bbox: tuple) -> np.ndarray:
        """
        Fallback mask generation using RT-DETR mask head if SAM2 fails or times out.
        """
        print(f"Running RT-DETR fallback for bbox: {bbox}")
        if MOCK_INFERENCE:
            # Generate a simple rectangular mock mask
            h_orig, w_orig = original_img.shape[:2]
            mask = np.zeros((h_orig, w_orig), dtype=np.uint8)
            x1, y1, x2, y2 = bbox
            mask[y1:y2, x1:x2] = 255
            return mask

        import cv2


        # If we had a true RT-DETR panoptic/instance segmentation model loaded,
        # we would extract the mask here. Since RT-DETR is primarily a detector,
        # a real fallback might just crop the box and apply a simpler traditional thresholding
        # or grab a segmentation head output if the model supports it.

        # We will fallback to a GrabCut algorithm bounded by the RT-DETR box as a realistic offline fallback
        h_orig, w_orig = original_img.shape[:2]

        # ⚡ Bolt Optimization: Crop the image to the bounding box region (with margin)
        # before running grabCut. Running grabCut on the full high-res array for a local box
        # is extremely slow O(H*W). Cropping gives significant speedups.
        x1, y1, x2, y2 = bbox
        margin = 50
        x1_crop = max(0, x1 - margin)
        y1_crop = max(0, y1 - margin)
        x2_crop = min(w_orig, x2 + margin)
        y2_crop = min(h_orig, y2 + margin)

        cropped_img = original_img[y1_crop:y2_crop, x1_crop:x2_crop]
        cropped_mask = np.zeros(cropped_img.shape[:2], np.uint8)

        # bg and fg models for grabCut
        bgdModel = np.zeros((1,65), np.float64)
        fgdModel = np.zeros((1,65), np.float64)

        # Rect format for grabCut is (x, y, w, h) in the local cropped coordinate space
        rect_cropped = (x1 - x1_crop, y1 - y1_crop, x2 - x1, y2 - y1)

        # Apply grabCut on the cropped region
        cv2.grabCut(cropped_img, cropped_mask, rect_cropped, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)

        # Modify mask such that all definite background and probable background are set to 0,
        # and definite foreground and probable foreground are set to 255
        cropped_binary = np.where((cropped_mask==2)|(cropped_mask==0), 0, 1).astype('uint8') * 255

        # Place the cropped binary mask back onto the full-sized mask
        binary_mask = np.zeros((h_orig, w_orig), dtype=np.uint8)
        binary_mask[y1_crop:y2_crop, x1_crop:x2_crop] = cropped_binary

        return binary_mask
