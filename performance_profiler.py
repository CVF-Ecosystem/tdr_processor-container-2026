"""
Performance Profiling Tool for TDR Processor

Identifies code bottlenecks using cProfile, memory profiling, and execution timing.
Generates reports to guide optimization efforts.

Phase 3.2: Performance Optimization
"""
import cProfile
import pstats
import io
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass, asdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from report_processor import ReportProcessor
from utils.file_utils import setup_project_directories


@dataclass
class PerformanceResult:
    """Performance measurement result."""
    operation: str
    execution_time: float
    memory_usage: Optional[float] = None
    cpu_percent: Optional[float] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class PerformanceProfiler:
    """Profiles code performance to identify bottlenecks."""
    
    def __init__(self, output_dir: str = "performance_reports"):
        """Initialize profiler.
        
        Args:
            output_dir: Directory to save performance reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[PerformanceResult] = []
        self.profiler = cProfile.Profile()
        self.profile_stats_file = None
    
    def profile_function(self, func, *args, **kwargs) -> Tuple[float, any]:
        """Profile a single function execution.
        
        Args:
            func: Function to profile
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Tuple of (execution_time, return_value)
        """
        start_time = time.time()
        self.profiler.enable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            self.profiler.disable()
        
        end_time = time.time()
        return (end_time - start_time, result)
    
    def save_profile_stats(self, filename: str, sort_by: str = 'cumulative') -> str:
        """Save profiler statistics to file.
        
        Args:
            filename: Output filename (without path)
            sort_by: Sort statistics by this field
        
        Returns:
            Path to saved report
        """
        output_file = self.output_dir / filename
        temp_stats_file = output_file.with_suffix('.prof')
        
        # Save profile data to temp file
        self.profiler.dump_stats(str(temp_stats_file))
        
        # Load and format stats
        with open(output_file, 'w') as f:
            ps = pstats.Stats(str(temp_stats_file), stream=f)
            ps.sort_stats(sort_by)
            ps.print_stats(30)  # Top 30 functions
        
        # Clean up temp file
        if temp_stats_file.exists():
            temp_stats_file.unlink()
        
        return str(output_file)
    
    def get_profile_stats_string(self, sort_by: str = 'cumulative') -> str:
        """Get profiler statistics as string.
        
        Args:
            sort_by: Sort statistics by this field
        
        Returns:
            Statistics as string
        """
        temp_stats_file = self.output_dir / ".temp_stats.prof"
        self.profiler.dump_stats(str(temp_stats_file))
        
        s = io.StringIO()
        try:
            ps = pstats.Stats(str(temp_stats_file), stream=s)
            ps.sort_stats(sort_by)
            ps.print_stats(30)  # Top 30 functions
        finally:
            if temp_stats_file.exists():
                temp_stats_file.unlink()
        
        return s.getvalue()
    
    def record_result(self, operation: str, execution_time: float) -> None:
        """Record a performance measurement.
        
        Args:
            operation: Operation name
            execution_time: Time taken in seconds
        """
        result = PerformanceResult(
            operation=operation,
            execution_time=execution_time
        )
        self.results.append(result)
        print(f"[PERF] {operation}: {execution_time:.4f}s")
    
    def save_results_json(self, filename: str = "performance_results.json") -> str:
        """Save results to JSON file.
        
        Args:
            filename: Output filename
        
        Returns:
            Path to saved file
        """
        output_file = self.output_dir / filename
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in self.results],
            "summary": {
                "total_operations": len(self.results),
                "total_time": sum(r.execution_time for r in self.results),
                "average_time": sum(r.execution_time for r in self.results) / len(self.results) if self.results else 0
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return str(output_file)
    
    def print_summary(self) -> None:
        """Print performance summary."""
        if not self.results:
            print("[PERF] No results recorded")
            return
        
        print("\n" + "="*80)
        print("PERFORMANCE SUMMARY")
        print("="*80)
        
        total_time = sum(r.execution_time for r in self.results)
        avg_time = total_time / len(self.results)
        
        print(f"Total Operations: {len(self.results)}")
        print(f"Total Time: {total_time:.4f}s")
        print(f"Average Time: {avg_time:.4f}s")
        print(f"Min Time: {min(self.results, key=lambda r: r.execution_time).execution_time:.4f}s")
        print(f"Max Time: {max(self.results, key=lambda r: r.execution_time).execution_time:.4f}s")
        
        print("\nTop 10 Slowest Operations:")
        sorted_results = sorted(self.results, key=lambda r: r.execution_time, reverse=True)
        for i, result in enumerate(sorted_results[:10], 1):
            percent = (result.execution_time / total_time) * 100
            print(f"  {i:2}. {result.operation:40} {result.execution_time:.4f}s ({percent:6.2f}%)")
        
        print("="*80 + "\n")


def profile_data_extraction(profiler: PerformanceProfiler) -> None:
    """Profile data extraction operations.
    
    Args:
        profiler: PerformanceProfiler instance
    """
    print("\n[PROFILING] Data Extraction Operations...")
    
    from data_extractors import DataExtractor
    
    # Find a sample Excel file
    data_input_dir = Path("data_input")
    if not data_input_dir.exists():
        print("[SKIP] data_input directory not found")
        return
    
    excel_files = list(data_input_dir.glob("*.xlsx"))
    if not excel_files:
        print("[SKIP] No Excel files found in data_input")
        return
    
    sample_file = excel_files[0]
    print(f"[PROFILE] Using sample file: {sample_file}")
    
    # Profile DataExtractor initialization
    start = time.time()
    extractor = DataExtractor(sample_file, sample_file)
    elapsed = time.time() - start
    profiler.record_result("DataExtractor.__init__()", elapsed)
    
    # Profile vessel info extraction
    start = time.time()
    vessel_data = extractor.extract_vessel_info()
    elapsed = time.time() - start
    profiler.record_result("extract_vessel_info()", elapsed)


def profile_dataframe_operations(profiler: PerformanceProfiler) -> None:
    """Profile pandas dataframe operations.
    
    Args:
        profiler: PerformanceProfiler instance
    """
    print("\n[PROFILING] DataFrame Operations...")
    
    import pandas as pd
    
    # Create test dataframe
    size = 10000
    test_df = pd.DataFrame({
        'id': range(size),
        'value': [float(i) * 1.5 for i in range(size)],
        'name': [f"item_{i}" for i in range(size)],
        'amount': [f"{i}.50" for i in range(size)]
    })
    
    # Profile apply_qc_calculations from dataframe_utils
    from utils.dataframe_utils import apply_qc_calculations
    
    # Create QC dataframe for testing
    qc_test_df = pd.DataFrame({
        'gross_working': [8.0] * 100,
        'delay_times': [1.5] * 100,
        'total_conts_qc': [100] * 100
    })
    
    start = time.time()
    result = apply_qc_calculations(qc_test_df.copy())
    elapsed = time.time() - start
    profiler.record_result(f"apply_qc_calculations (n={len(qc_test_df)})", elapsed)
    
    # Profile format_dataframe_numeric_columns
    from utils.dataframe_utils import format_dataframe_numeric_columns
    
    numeric_cols = ['id', 'value']
    start = time.time()
    result = format_dataframe_numeric_columns(test_df.copy(), numeric_cols)
    elapsed = time.time() - start
    profiler.record_result(f"format_dataframe_numeric_columns (n={size}, cols=2)", elapsed)
    
    # Profile copy operation (baseline)
    start = time.time()
    result = test_df.copy()
    elapsed = time.time() - start
    profiler.record_result(f"DataFrame.copy() (n={size}, cols=4)", elapsed)
    
    # Profile group by operation
    start = time.time()
    result = test_df.groupby('name').agg({'value': 'sum', 'id': 'count'})
    elapsed = time.time() - start
    profiler.record_result(f"DataFrame.groupby().agg() (n={size}, groups={len(result)})", elapsed)


def profile_report_processing(profiler: PerformanceProfiler) -> None:
    """Profile report processing pipeline.
    
    Args:
        profiler: PerformanceProfiler instance
    """
    print("\n[PROFILING] Report Processing Pipeline...")
    
    # Find sample input file
    data_input_dir = Path("data_input")
    if not data_input_dir.exists():
        print("[SKIP] data_input directory not found")
        return
    
    excel_files = list(data_input_dir.glob("*.xlsx"))
    if not excel_files:
        print("[SKIP] No Excel files found")
        return
    
    input_file = str(excel_files[0])
    output_file = "outputs/perf_test_report.xlsx"
    
    print(f"[PROFILE] Processing: {input_file}")
    
    processor = ReportProcessor()
    
    # Profile full processing
    start = time.time()
    profiler.profiler.enable()
    try:
        success = processor.process_report(input_file, output_file)
    finally:
        profiler.profiler.disable()
    elapsed = time.time() - start
    
    if success:
        profiler.record_result("process_report() - Full Pipeline", elapsed)
        
        # Check output file size
        if Path(output_file).exists():
            file_size = Path(output_file).stat().st_size / 1024 / 1024  # MB
            print(f"[PROFILE] Output file size: {file_size:.2f} MB")
    else:
        print("[SKIP] Report processing failed")


def profile_excel_writing(profiler: PerformanceProfiler) -> None:
    """Profile Excel file writing operations.
    
    Args:
        profiler: PerformanceProfiler instance
    """
    print("\n[PROFILING] Excel Writing Operations...")
    
    import pandas as pd
    
    # Create test dataframe
    size = 5000
    test_df = pd.DataFrame({
        f'col_{i}': range(size) for i in range(10)
    })
    
    output_file = "outputs/perf_test_write.xlsx"
    
    # Profile Excel write
    start = time.time()
    test_df.to_excel(output_file, index=False)
    elapsed = time.time() - start
    profiler.record_result(f"DataFrame.to_excel() (n={size}, cols=10)", elapsed)
    
    # Clean up
    if Path(output_file).exists():
        Path(output_file).unlink()


def main():
    """Run comprehensive performance profiling."""
    print("="*80)
    print("TDR PROCESSOR - PERFORMANCE PROFILING")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Setup - data_csv and data_excel are inside outputs folder
    required_dirs = ["data_input", "backup", "outputs", "templates"]
    setup_project_directories(Path.cwd(), required_dirs)
    config.load_environment_config()
    profiler = PerformanceProfiler()
    
    # Run profiling
    try:
        profile_dataframe_operations(profiler)
        profile_excel_writing(profiler)
        profile_data_extraction(profiler)
        profile_report_processing(profiler)
    except Exception as e:
        print(f"\n[ERROR] Profiling failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Generate reports
    print("\n[REPORT] Generating performance reports...")
    
    stats_file = profiler.save_profile_stats("profile_stats.txt")
    print(f"[REPORT] Saved: {stats_file}")
    
    results_file = profiler.save_results_json()
    print(f"[REPORT] Saved: {results_file}")
    
    # Print summary
    profiler.print_summary()
    
    # Print detailed stats
    print("\n" + "="*80)
    print("DETAILED PROFILER STATISTICS (Top 30 by Cumulative Time)")
    print("="*80)
    print(profiler.get_profile_stats_string('cumulative'))
    
    print("="*80)
    print("PERFORMANCE PROFILING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
