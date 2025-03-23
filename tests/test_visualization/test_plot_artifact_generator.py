import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from flask import Flask, jsonify
import json

# Create a test Flask app
flask_app = Flask(__name__)

# Import the function to test AFTER app creation
with flask_app.app_context():
    from app.backend.visualization.plot_artifact_generator import (
        generate_visualization_artifacts,
    )

from app.backend.llm_engine import get_llm


class TestVisualizationArtifactGeneration(unittest.TestCase):
    """Test suite for visualization artifact generation pipeline"""

    @classmethod
    def setUpClass(cls):
        """Ensure the LLM instance is initialized before running tests."""
        get_llm()

    def setUp(self):
        """Create sample valid execution data"""
        self.valid_execution = {
            "columns": ["category", "value"],
            "data": [["A", 10], ["B", 20], ["C", 30]],
        }

        self.mock_plot_config = {
            "plot_type": "plot_bar",
            "arguments": {"category_column": "category", "value_column": "value"},
        }

        # Create a test client
        self.app = flask_app.test_client()
        self.app.testing = True

    def test_happy_path_artifact_generation(self):
        """Test successful end-to-end artifact generation"""
        with flask_app.app_context(), patch(
            "app.backend.visualization.plot_artifact_generator.build_visualization_context"
        ) as mock_build, patch(
            "app.backend.visualization.plot_artifact_generator.format_plot_selection_instructions"
        ) as mock_format, patch(
            "app.backend.visualization.plot_artifact_generator.generate_plot_json"
        ) as mock_generate:

            # Setup mocks
            mock_build.return_value = {"compatible_plots": [], "data_context": {}}
            mock_format.return_value = "formatted_instructions"
            mock_generate.return_value = jsonify({"plot": "success"})

            # Execute
            response = generate_visualization_artifacts(self.valid_execution)

            # Verify
            mock_build.assert_called_once_with(self.valid_execution)
            mock_format.assert_called_once_with(mock_build.return_value)

            # Get the actual call arguments
            self.assertEqual(mock_generate.call_count, 1)
            call_args = mock_generate.call_args[0]

            # Verify positional arguments
            self.assertEqual(call_args[0], self.valid_execution)
            self.assertEqual(call_args[1], "formatted_instructions")
            self.assertEqual(call_args[2], mock_build.return_value)

            # Verify DataFrame equality separately
            expected_df = pd.DataFrame(
                self.valid_execution["data"], columns=self.valid_execution["columns"]
            )
            pd.testing.assert_frame_equal(call_args[3], expected_df)

            self.assertEqual(response.status_code, 200)

    def test_missing_data_key(self):
        """Test handling of execution data with missing 'data' key"""
        with flask_app.app_context():
            invalid_execution = {"columns": ["test"]}
            response = generate_visualization_artifacts(invalid_execution)
            response_data = response.get_json()

            self.assertIn("error", response_data)
            self.assertIn("Missing data in session", response_data["error"])
            self.assertEqual(response.status_code, 200)

    def test_missing_columns_key(self):
        """Test handling of execution data with missing 'columns' key"""
        with flask_app.app_context():
            invalid_execution = {"data": [[1], [2]]}
            response = generate_visualization_artifacts(invalid_execution)
            response_data = response.get_json()

            self.assertIn("error", response_data)
            self.assertIn("Missing data in session", response_data["error"])
            self.assertEqual(response.status_code, 200)

    def test_empty_data_handling(self):
        """Test handling of empty dataset in execution result"""
        with flask_app.app_context(), patch(
            "app.backend.visualization.plot_artifact_generator.build_visualization_context"
        ) as mock_build:

            empty_execution = {"columns": ["test"], "data": []}
            mock_build.return_value = {
                "compatible_plots": [],
                "data_context": {
                    "row_count": 0,
                    "columns": {"test": "object"},
                    "sample_3_values": {"test": []},
                },
            }

            response = generate_visualization_artifacts(empty_execution)
            response_data = response.get_json()

            self.assertIn("compatible_plots_error", response_data)
            self.assertEqual(response.status_code, 200)

    def test_error_propagation_from_context_building(self):
        """Test error propagation from visualization context building"""
        with flask_app.app_context(), patch(
            "app.backend.visualization.plot_artifact_generator.build_visualization_context"
        ) as mock_build:

            # Mock the context building to return an error
            mock_build.return_value = {
                "compatible_plots": [],
                "data_context": {},
                "error": "Context building failed",
            }

            response = generate_visualization_artifacts(self.valid_execution)
            response_data = response.get_json()

            self.assertIn("error", response_data)
            self.assertIn("Context building failed", response_data["error"])

    def test_llm_fallback_mechanism(self):
        """Test LLM failure triggers fallback configuration"""

        with flask_app.app_context(), patch(
            "app.backend.llm_engine.LLM.create_completion"
        ) as mock_llm:

            mock_llm.side_effect = Exception("LLM failure")
            response = generate_visualization_artifacts(self.valid_execution)

            self.assertIn("Histogram Chart", response)

            response_dict = json.loads(response)

            # Verify plot contains both histogram bars and density line
            renderers = response_dict["doc"]["roots"][0]["attributes"]["renderers"]
            self.assertEqual(
                len(renderers), 2, "Should have 2 renderers (histogram + line)"
            )

            # Validate histogram quad properties
            histogram = renderers[0]["attributes"]
            self.assertEqual(histogram["glyph"]["name"], "Quad")
            data_source = histogram["data_source"]["attributes"]["data"]
            data_keys = [entry[0] for entry in data_source["entries"]]
            self.assertIn("left", data_keys)
            self.assertIn("right", data_keys)
            self.assertIn("top", data_keys)

            # Validate density line properties
            line = renderers[1]["attributes"]
            self.assertEqual(line["glyph"]["name"], "Line")
            line_data = line["data_source"]["attributes"]["data"]
            line_keys = [entry[0] for entry in line_data["entries"]]
            self.assertIn("x", line_keys)
            self.assertIn("y", line_keys)

            # Check axis configuration
            figure_attrs = response_dict["doc"]["roots"][0]["attributes"]
            self.assertEqual(
                figure_attrs["below"][0]["attributes"]["axis_label"], "value"
            )
            self.assertEqual(
                figure_attrs["left"][0]["attributes"]["axis_label"], "Density"
            )

    def test_dataframe_injection(self):
        """Test DataFrame is properly injected into plot arguments"""
        with flask_app.app_context(), patch(
            "app.backend.visualization.plot_artifact_generator.generate_plot_json"
        ) as mock_generate:

            expected_df = pd.DataFrame(
                self.valid_execution["data"], columns=self.valid_execution["columns"]
            )

            generate_visualization_artifacts(self.valid_execution)
            call_args = mock_generate.call_args[0]

            pd.testing.assert_frame_equal(call_args[3], expected_df)

    def test_error_handling_in_json_generation(self):
        """Test error handling during final JSON generation"""
        with flask_app.app_context(), patch(
            "app.backend.visualization.plot_artifact_generator.generate_plot_json"
        ) as mock_generate:

            mock_generate.return_value = jsonify({"error": "Rendering failed"})
            response = generate_visualization_artifacts(self.valid_execution)
            response_data = response.get_json()

            self.assertIn("error", response_data)
            self.assertEqual(response.status_code, 200)

    def test_invalid_data_types_handling(self):
        """Test handling of invalid data types in execution result"""
        with flask_app.app_context():
            invalid_execution = {
                "columns": ["valid_col"],
                "data": [[1], ["string"]],  # Inconsistent data types
            }

            response = generate_visualization_artifacts(invalid_execution)
            response_data = response.get_json()

            self.assertIn("compatible_plots_error", response_data)
            self.assertEqual(response.status_code, 200)

    def test_multi_column_dataset_handling(self):
        """Test handling of datasets with multiple columns"""
        with flask_app.app_context(), patch(
            "app.backend.visualization.plot_artifact_generator.generate_plot_json"
        ) as mock_generate:

            complex_execution = {
                "columns": ["cat1", "cat2", "num1", "num2"],
                "data": [["A", "X", 10, 20], ["B", "Y", 30, 40]],
            }

            mock_generate.return_value = jsonify({"plot": "success"})
            response = generate_visualization_artifacts(complex_execution)
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
