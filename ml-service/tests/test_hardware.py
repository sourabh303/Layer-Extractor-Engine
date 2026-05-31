import pytest
from unittest.mock import patch
import os
from utils.hardware import get_hardware_mode, get_execution_providers, quantize_onnx_model_int8

def test_get_hardware_mode_gpu(mocker):
    # Mock ort.get_available_providers to return CUDA
    mocker.patch('utils.hardware.ort.get_available_providers', return_value=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    mode = get_hardware_mode()
    assert mode == "GPU"

def test_get_hardware_mode_cpu(mocker):
    # Mock ort.get_available_providers to return only CPU
    mocker.patch('utils.hardware.ort.get_available_providers', return_value=['CPUExecutionProvider'])
    mode = get_hardware_mode()
    assert mode == "CPU"

def test_get_hardware_mode_empty(mocker):
    # Mock ort.get_available_providers to return empty list
    mocker.patch('utils.hardware.ort.get_available_providers', return_value=[])
    mode = get_hardware_mode()
    assert mode == "CPU"

def test_get_execution_providers_gpu(mocker):
    # Mock get_hardware_mode to return GPU
    mocker.patch('utils.hardware.get_hardware_mode', return_value="GPU")
    providers = get_execution_providers()
    assert providers == ['CUDAExecutionProvider', 'CPUExecutionProvider']

def test_get_execution_providers_cpu(mocker):
    # Mock get_hardware_mode to return CPU
    mocker.patch('utils.hardware.get_hardware_mode', return_value="CPU")
    providers = get_execution_providers()
    assert providers == ['CPUExecutionProvider']

def test_quantize_onnx_model_int8_success(mocker):
    # Mock os.path.exists to return True
    mocker.patch('os.path.exists', return_value=True)

    # Mock the quantization module
    mock_quantize = mocker.patch('onnxruntime.quantization.quantize_dynamic')

    input_model = "dummy_input.onnx"
    output_model = "dummy_output.onnx"

    quantize_onnx_model_int8(input_model, output_model)

    # Check that quantize_dynamic was called with the correct arguments
    # Note: We need to import QuantType here to assert against it, or check the kwargs
    from onnxruntime.quantization import QuantType
    mock_quantize.assert_called_once_with(
        input_model,
        output_model,
        weight_type=QuantType.QInt8
    )

def test_quantize_onnx_model_int8_file_not_found(mocker, capsys):
    # Mock os.path.exists to return False
    mocker.patch('os.path.exists', return_value=False)

    input_model = "missing_input.onnx"
    output_model = "missing_output.onnx"

    # The quantize module should still be available in the mock env, but we mock it just in case to ensure it's not called
    mock_quantize = mocker.patch('onnxruntime.quantization.quantize_dynamic')

    quantize_onnx_model_int8(input_model, output_model)

    mock_quantize.assert_not_called()

    # Check stdout
    captured = capsys.readouterr()
    assert f"Model path {input_model} does not exist." in captured.out

def test_quantize_onnx_model_int8_import_error(monkeypatch, capsys):
    # Instead of mocker, use sys.modules to simulate an ImportError
    import sys

    # Force ImportError when onnxruntime.quantization is imported
    # We patch builtins.__import__ to raise ImportError specifically for onnxruntime.quantization

    original_import = __import__
    def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'onnxruntime.quantization' or (name == 'onnxruntime' and fromlist and 'quantization' in fromlist):
            raise ImportError("Mocked ImportError")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr('builtins.__import__', mock_import)

    input_model = "dummy.onnx"
    output_model = "dummy_out.onnx"

    quantize_onnx_model_int8(input_model, output_model)

    captured = capsys.readouterr()
    assert "ONNX Runtime quantization tools not available." in captured.out
