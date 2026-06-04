import pytest
from unittest.mock import patch
from pipeline.vectorization import VectorizationPipeline

def test_process_layer_to_svg_calls_vtracer_with_correct_args():
    input_path = "dummy_input.png"
    output_path = "dummy_output.svg"

    with patch("pipeline.vectorization.vtracer.convert_image_to_svg_py") as mock_vtracer:
        result = VectorizationPipeline.process_layer_to_svg(input_path, output_path)

        assert result == output_path
        mock_vtracer.assert_called_once_with(
            input_path,
            output_path,
            colormode="color",
            hierarchical="stacked",
            mode="polygon",
            filter_speckle=4,
            color_precision=8,
            layer_difference=16,
            corner_threshold=60,
            length_threshold=4.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=8,
            curve_fitting=False
        )
