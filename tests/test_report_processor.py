import pytest
from report_processor import ReportProcessor
from pathlib import Path
import os


def test_report_processor_init(tmp_path):
    """Test that ReportProcessor initializes correctly and creates output directories."""
    input_dir = tmp_path / "data_input"
    input_dir.mkdir()
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    processor = ReportProcessor(input_dir=str(input_dir), output_dir=str(output_dir))

    assert processor.input_dir == input_dir
    assert processor.output_dir == output_dir
    assert (output_dir / "data_excel").exists()
    assert (output_dir / "data_csv").exists()


def test_report_processor_process_tdr_files_empty(tmp_path):
    """Test process_tdr_files returns correct result when given empty file list."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    processor = ReportProcessor(output_dir=str(output_dir))
    result = processor.process_tdr_files([])

    assert result["processed_count"] == 0
    assert result["skipped_count"] == 0


def test_report_processor_process_tdr_files_invalid_file(tmp_path):
    """Test process_tdr_files handles invalid Excel files gracefully."""
    input_dir = tmp_path / "data_input"
    input_dir.mkdir()
    # Create a fake (invalid) xlsx file
    sample_file = input_dir / "sample.xlsx"
    sample_file.write_bytes(b"PK\x03\x04Fake Excel content")  # ZIP magic bytes but invalid content

    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    processor = ReportProcessor(input_dir=str(input_dir), output_dir=str(output_dir))
    result = processor.process_tdr_files([sample_file])

    # Should handle gracefully - either processed or skipped, but no unhandled exception
    assert "processed_count" in result
    assert "skipped_count" in result
    assert "message" in result


def test_required_directories_created(tmp_path):
    """Test that setup_project_directories creates all required directories."""
    from utils.file_utils import setup_project_directories
    required_dirs = ["data_input", "data_excel", "data_csv", "backup", "outputs", "templates"]
    result = setup_project_directories(tmp_path, required_dirs)
    for d in required_dirs:
        assert (tmp_path / d).exists()
    assert result
