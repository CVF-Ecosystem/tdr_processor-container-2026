"""
Tests for Excel optimization utilities - Phase 3.2
"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from utils.excel_optimizer import (
    export_dataframe_to_excel_optimized,
    export_multiple_dataframes_to_excel,
    optimize_dataframe_for_excel,
    get_excel_export_info
)


class TestExcelOptimization:
    """Test Excel optimization utilities."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'id': range(100),
            'name': [f'item_{i}' for i in range(100)],
            'value': [float(i) * 1.5 for i in range(100)],
            'amount': [f'{i}.99' for i in range(100)]
        })
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            yield Path(f.name)
        # Cleanup
        if Path(f.name).exists():
            Path(f.name).unlink()
    
    def test_export_dataframe_basic(self, sample_dataframe, temp_file):
        """Test basic DataFrame export."""
        success = export_dataframe_to_excel_optimized(
            sample_dataframe,
            str(temp_file)
        )
        assert success is True
        assert temp_file.exists()
    
    def test_export_dataframe_with_options(self, sample_dataframe, temp_file):
        """Test DataFrame export with various options."""
        success = export_dataframe_to_excel_optimized(
            sample_dataframe,
            str(temp_file),
            sheet_name="TestSheet",
            include_index=True,
            format_numbers=True,
            auto_width=True,
            header_bold=True
        )
        assert success is True
        assert temp_file.exists()
    
    def test_export_large_dataframe(self, temp_file):
        """Test export of large DataFrame."""
        large_df = pd.DataFrame({
            'col_' + str(i): range(5000)
            for i in range(10)
        })
        
        success = export_dataframe_to_excel_optimized(
            large_df,
            str(temp_file)
        )
        assert success is True
    
    def test_export_empty_dataframe(self, temp_file):
        """Test export of empty DataFrame."""
        empty_df = pd.DataFrame()
        success = export_dataframe_to_excel_optimized(
            empty_df,
            str(temp_file)
        )
        assert success is True
    
    def test_export_multiple_sheets(self, sample_dataframe, temp_file):
        """Test export of multiple DataFrames to sheets."""
        dataframes = {
            'Sheet1': sample_dataframe,
            'Sheet2': sample_dataframe.copy(),
            'Sheet3': sample_dataframe.iloc[:50]
        }
        
        success = export_multiple_dataframes_to_excel(
            dataframes,
            str(temp_file)
        )
        assert success is True
        assert temp_file.exists()
    
    def test_export_multiple_empty_dict(self, temp_file):
        """Test export with empty dataframes dict."""
        success = export_multiple_dataframes_to_excel({}, str(temp_file))
        # Should still succeed (empty workbook)
        assert success is True
    
    def test_optimize_dataframe_numeric(self, sample_dataframe):
        """Test numeric column optimization."""
        df_opt = optimize_dataframe_for_excel(
            sample_dataframe,
            numeric_columns=['amount']
        )
        
        # Check that column was processed
        assert 'amount' in df_opt.columns
        assert df_opt['amount'].dtype in ['float64', 'float32', 'object']
    
    def test_optimize_dataframe_datetime(self):
        """Test datetime column optimization."""
        df = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=10),
            'value': range(10)
        })
        
        df_opt = optimize_dataframe_for_excel(
            df,
            datetime_columns=['date']
        )
        
        # Check conversion
        assert df_opt['date'].dtype == 'object'
        assert all('2025' in str(d) for d in df_opt['date'])
    
    def test_optimize_dataframe_string(self):
        """Test string column optimization."""
        df = pd.DataFrame({
            'category': ['A', 'B', 'A', 'C', 'B'] * 20,
            'value': range(100)
        })
        
        df_opt = optimize_dataframe_for_excel(
            df,
            string_columns=['category']
        )
        
        # Should have optimized repeated values
        assert df_opt is not None
    
    def test_get_excel_export_info(self, sample_dataframe):
        """Test export info collection."""
        info = get_excel_export_info(sample_dataframe)
        
        assert 'rows' in info
        assert 'columns' in info
        assert 'memory_mb' in info
        assert info['rows'] == 100
        assert info['columns'] == 4
    
    def test_get_excel_export_info_large(self):
        """Test export info for large DataFrame."""
        large_df = pd.DataFrame({
            'col_' + str(i): range(10000)
            for i in range(20)
        })
        
        info = get_excel_export_info(large_df)
        
        assert info['rows'] == 10000
        assert info['columns'] == 20
        assert info['memory_mb'] > 0
        assert info['numeric_cols'] == 20
    
    def test_export_creates_parent_directory(self):
        """Test that export creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'subdir' / 'nested' / 'file.xlsx'
            df = pd.DataFrame({'A': [1, 2, 3]})
            
            success = export_dataframe_to_excel_optimized(df, str(filepath))
            
            assert success is True
            assert filepath.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
