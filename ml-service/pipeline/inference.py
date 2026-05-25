import os
import asyncio
import numpy as np
from PIL import Image

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

    def run_rt_detr_detection(self, image_path: str) -> list[tuple]:
        """
        Runs RT-DETR to detect motifs and returns a list of bounding boxes.
        Returns: [(x1, y1, x2, y2), ...]
        """
        if MOCK_INFERENCE:
            # Mock 2 bounding boxes for testing
            img = Image.open(image_path)
            w, h = img.size
            return [
                (int(w*0.1), int(h*0.1), int(w*0.4), int(h*0.4)),
                (int(w*0.5), int(h*0.5), int(w*0.9), int(h*0.9))
            ]

        import cv2
        import numpy as np

        if not self.rt_detr_session:
            raise RuntimeError("RT-DETR session not loaded.")

        # 1. Preprocess Image
        # Assuming typical RT-DETR preprocessing: resize to 640x640, normalize, CHW format
        original_img = cv2.imread(image_path)
        if original_img is None:
            raise ValueError("Could not read image for RT-DETR.")

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

        bboxes = []
        conf_threshold = 0.5

        for pred in predictions:
            # Format varies, assuming [x, y, w, h, conf, class1, class2...]
            # or [x1, y1, x2, y2, conf, class]
            if len(pred) >= 6:
                # If it's x, y, w, h format (normalized 0-1)
                x_c, y_c, w, h_box, conf = pred[0:5]

                # Check if conf is actually a score or if we need to take max of class scores
                score = conf if conf <= 1.0 else np.max(pred[5:])

                if score > conf_threshold:
                    # Convert from normalized cx,cy,w,h to absolute x1,y1,x2,y2
                    x1 = int((x_c - w/2) * w_orig)
                    y1 = int((y_c - h_box/2) * h_orig)
                    x2 = int((x_c + w/2) * w_orig)
                    y2 = int((y_c + h_box/2) * h_orig)

                    # Clamp to image boundaries
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(w_orig, x2), min(h_orig, y2)

                    bboxes.append((x1, y1, x2, y2))

        return bboxes

    async def run_sam2_segmentation(self, image_path: str, bbox: tuple) -> np.ndarray:
        """
        Runs SAM2 inference asynchronously to generate a high-quality segmentation mask.
        Returns a binary numpy array (mask).
        """
        if MOCK_INFERENCE:
            # Simulate processing time
            await asyncio.sleep(1.0)

            # Generate a mock circular mask inside the bbox
            img = Image.open(image_path)
            w, h = img.size
            mask = np.zeros((h, w), dtype=np.uint8)
            x1, y1, x2, y2 = bbox
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            r = min(x2 - x1, y2 - y1) // 2

            y, x = np.ogrid[:h, :w]
            dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)
            mask[dist_from_center <= r] = 255

            return mask

        import torch
        import cv2
        import numpy as np

        if not self.sam2_model:
            raise RuntimeError("SAM2 model not loaded.")

        # Run inside an executor since PyTorch inference is blocking CPU/GPU bound
        loop = asyncio.get_running_loop()

        def _sync_sam2_inference():
            original_img = cv2.imread(image_path)
            if original_img is None:
                raise ValueError("Could not read image for SAM2.")

            img = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
            h_orig, w_orig = img.shape[:2]

            # Assuming typical SAM predictor pattern wrapped in our loaded model
            # 1. Set Image (Embeddings calculation)
            # Depending on SAM2 API, it might expect a tensor or numpy array

            # Mocking the typical torch vision preprocessing for the raw model:
            # Real SAM uses a complex predictor class, we'll emulate the tensor forward pass
            device = next(self.sam2_model.parameters()).device

            # Resize image to SAM expected input size (e.g., 1024x1024)
            # In a real implementation this uses the SAM ResizeLongestSide transform
            input_image = cv2.resize(img, (1024, 1024))
            input_tensor = torch.as_tensor(input_image, device=device).permute(2, 0, 1).unsqueeze(0).float()

            # Normalize bounding box for the 1024x1024 scale
            x1, y1, x2, y2 = bbox
            scale_x = 1024 / w_orig
            scale_y = 1024 / h_orig
            box_1024 = torch.tensor([[x1*scale_x, y1*scale_y, x2*scale_x, y2*scale_y]], device=device)

            with torch.no_grad():
                # Forward pass: getting image embeddings and decoding masks
                # (Actual SAM2 API uses build_sam2_predictor and predictor.set_image(), predictor.predict())
                # Here we pass the tensor and box directly to the loaded model representation
                masks, scores, _ = self.sam2_model(input_tensor, boxes=box_1024)

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

    def run_rt_detr_fallback_mask(self, image_path: str, bbox: tuple) -> np.ndarray:
        """
        Fallback mask generation using RT-DETR mask head if SAM2 fails or times out.
        """
        print(f"Running RT-DETR fallback for bbox: {bbox}")
        if MOCK_INFERENCE:
            # Generate a simple rectangular mock mask
            img = Image.open(image_path)
            w, h = img.size
            mask = np.zeros((h, w), dtype=np.uint8)
            x1, y1, x2, y2 = bbox
            mask[y1:y2, x1:x2] = 255
            return mask

        import cv2
        import numpy as np

        # If we had a true RT-DETR panoptic/instance segmentation model loaded,
        # we would extract the mask here. Since RT-DETR is primarily a detector,
        # a real fallback might just crop the box and apply a simpler traditional thresholding
        # or grab a segmentation head output if the model supports it.

        # We will fallback to a GrabCut algorithm bounded by the RT-DETR box as a realistic offline fallback
        original_img = cv2.imread(image_path)
        if original_img is None:
            raise ValueError("Could not read image for RT-DETR fallback.")

        h_orig, w_orig = original_img.shape[:2]
        mask = np.zeros((h_orig, w_orig), np.uint8)

        # bg and fg models for grabCut
        bgdModel = np.zeros((1,65), np.float64)
        fgdModel = np.zeros((1,65), np.float64)

        # Rect format for grabCut is (x, y, w, h)
        x1, y1, x2, y2 = bbox
        rect = (x1, y1, x2 - x1, y2 - y1)

        # Apply grabCut
        cv2.grabCut(original_img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)

        # Modify mask such that all definite background and probable background are set to 0,
        # and definite foreground and probable foreground are set to 255
        binary_mask = np.where((mask==2)|(mask==0), 0, 1).astype('uint8') * 255

        return binary_mask
