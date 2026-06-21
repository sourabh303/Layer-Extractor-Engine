import onnxruntime as ort
import os

def get_hardware_mode() -> str:
    """
    Detects if CUDA is available and returns the appropriate hardware mode.
    Returns "GPU" if CUDAExecutionProvider is available, otherwise "CPU".
    """
    try:
        available_providers = ort.get_available_providers()
        if available_providers and 'CUDAExecutionProvider' in available_providers:
            return "GPU"
    except Exception:
        pass
    return "CPU"

def get_execution_providers() -> list:
    """
    Returns the list of execution providers to use based on available hardware.
    """
    mode = get_hardware_mode()
    if mode == "GPU":
        return ['CUDAExecutionProvider', 'CPUExecutionProvider']
    return ['CPUExecutionProvider']

def quantize_onnx_model_int8(input_model_path: str, output_model_path: str):
    """
    Scaffolding for dynamic INT8 quantization of ONNX models to reduce memory footprint.
    This fulfills the Phase 1 requirement for the memory-constrained design.
    Actual instantiation/usage of models will happen in Phase 2.
    """
    try:
        from onnxruntime.quantization import quantize_dynamic, QuantType
    except ImportError:
        print("ONNX Runtime quantization tools not available.")
        return

    if not os.path.exists(input_model_path):
        print(f"Model path {input_model_path} does not exist.")
        return

    print(f"Quantizing {input_model_path} to {output_model_path}...")
    quantize_dynamic(
        input_model_path,
        output_model_path,
        weight_type=QuantType.QInt8
    )
    print("Quantization complete.")
