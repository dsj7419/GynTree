# runners.py

import abc
import logging
import signal
import subprocess
import sys
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import psutil
import pytest
from contextlib import contextmanager
import tempfile
import shutil
import json
import queue
import os

logger = logging.getLogger(__name__)

class TestExecutionError(Exception):
    """Custom exception for test execution errors"""
    pass

@contextmanager
def timeout_handler(seconds: int):
    """Context manager for handling timeouts"""
    def signal_handler(signum, frame):
        raise TimeoutError(f"Test execution timed out after {seconds} seconds")
    
    # Save the previous handler
    previous_handler = signal.signal(signal.SIGALRM, signal_handler)
    
    try:
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)

class TestRunnerBase(abc.ABC):
    """Enhanced base class for test runners"""
    
    def __init__(self):
        self.temp_dir = None
        self.result_queue = queue.Queue()
    
    def _create_temp_dir(self) -> Path:
        """Create temporary directory for test artifacts"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="gyntree_test_"))
        return self.temp_dir
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @abc.abstractmethod
    def run(self, options: Dict[str, Any], selected_tests: Optional[List[str]], 
           reports_dir: str) -> 'TestResult':
        """Run tests with enhanced error handling and reporting"""
        pass
    
    def _build_pytest_args(self, options: Dict[str, Any], 
                         selected_tests: Optional[List[str]], 
                         reports_dir: str) -> List[str]:
        """Build pytest command line arguments with enhanced options"""
        pytest_args = [
            "-v",
            "--tb=short",
            "--capture=no",
            "--log-cli-level=debug" if options.get('debug') else "--log-cli-level=info",
            "--show-capture=all",  # Show stdout/stderr even for passing tests
            "--durations=10",  # Show 10 slowest tests
            "-rf",  # Show extra test summary info for failed tests
        ]
        
        # Add parallel execution if requested
        if options.get('parallel', False):
            worker_count = min(os.cpu_count() or 1, 4)  # Limit to 4 workers max
            pytest_args.extend(["-n", str(worker_count)])
        
        # Add HTML reporting
        if options.get('html_report', False):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_name = (f"{reports_dir}/test_report_"
                         f"{self.__class__.__name__.lower()}_{timestamp}.html")
            pytest_args.extend([
                f"--html={report_name}",
                "--self-contained-html"
            ])
        
        # Add coverage reporting
        if options.get('coverage', False):
            pytest_args.extend([
                "--cov=src",
                "--cov-report=term-missing",
                f"--cov-report=html:{reports_dir}/coverage",
                "--cov-branch",  # Enable branch coverage
                "--cov-report=xml:coverage.xml"  # For CI integration
            ])
        
        # Add test timeout configurations
        timeout = options.get('timeout', 300)
        pytest_args.extend([
            f"--timeout={timeout}",
            "--timeout-method=thread",
            "--timeout_func_only"
        ])
        
        # Add specific tests or test directory
        if selected_tests:
            pytest_args.extend(selected_tests)
        else:
            pytest_args.append("tests")
        
        # Add any extra arguments
        if options.get('extra_args'):
            pytest_args.extend(options['extra_args'].split())
        
        return pytest_args
    
    def _handle_test_output(self, output_file: Path) -> Dict[str, Any]:
        """Process test output file and extract relevant information"""
        if not output_file.exists():
            return {"error": "No test output file found"}
        
        result_data = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "warnings": [],
            "failed_tests": []
        }
        
        try:
            with output_file.open('r', encoding='utf-8') as f:
                for line in f:
                    if "PASSED" in line:
                        result_data["passed"] += 1
                    elif "FAILED" in line:
                        result_data["failed"] += 1
                        result_data["failed_tests"].append(line.strip())
                    elif "ERROR" in line:
                        result_data["errors"] += 1
                        result_data["failed_tests"].append(line.strip())
                    elif "SKIPPED" in line:
                        result_data["skipped"] += 1
                    elif "Warning" in line:
                        result_data["warnings"].append(line.strip())
        except Exception as e:
            logger.error(f"Error processing test output: {e}")
            result_data["error"] = str(e)
        
        return result_data
    
    def _cleanup_processes(self):
        """Clean up any remaining test processes"""
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        
        for child in children:
            try:
                child.terminate()
                child.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass

class TestResult:
    """Enhanced test result class with detailed information"""
    
    def __init__(self, success: bool = False, message: str = "", 
                 duration: float = 0.0, coverage: Optional[float] = None,
                 failed_tests: List[str] = None, warnings: List[str] = None,
                 error: Optional[str] = None):
        self.success = success
        self.message = message
        self.duration = duration
        self.coverage = coverage
        self.failed_tests = failed_tests or []
        self.warnings = warnings or []
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test result to dictionary format"""
        return {
            'success': self.success,
            'message': self.message,
            'duration': self.duration,
            'coverage': self.coverage,
            'failed_tests': self.failed_tests,
            'warnings': self.warnings,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """Create TestResult instance from dictionary"""
        result = cls(
            success=data.get('success', False),
            message=data.get('message', ''),
            duration=data.get('duration', 0.0),
            coverage=data.get('coverage'),
            failed_tests=data.get('failed_tests', []),
            warnings=data.get('warnings', []),
            error=data.get('error')
        )
        if 'timestamp' in data:
            result.timestamp = datetime.fromisoformat(data['timestamp'])
        return result

class AllTestsRunner(TestRunnerBase):
    """Runner for all tests with enhanced error handling"""
    
    def run(self, options: Dict[str, Any], selected_tests: Optional[List[str]], 
            reports_dir: str) -> TestResult:
        logger.info("Running all tests")
        temp_dir = None
        
        try:
            temp_dir = self._create_temp_dir()
            pytest_args = self._build_pytest_args(options, selected_tests, reports_dir)
            command = ["pytest"] + pytest_args
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = Path(reports_dir) / f"test_output_all_{timestamp}.txt"
            
            start_time = datetime.now()
            
            # Run tests with timeout
            with timeout_handler(options.get('timeout', 300)):
                process = psutil.Popen(
                    command,
                    stdout=output_file.open('w', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                try:
                    process.wait(timeout=options.get('timeout', 300))
                except psutil.TimeoutExpired:
                    process.kill()
                    raise TestExecutionError("Test execution timed out")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Process results
            result_data = self._handle_test_output(output_file)
            
            success = (process.returncode == 0 and 
                      result_data.get('failed', 0) == 0 and
                      result_data.get('errors', 0) == 0)
            
            return TestResult(
                success=success,
                message="Tests completed successfully" if success else "Tests failed",
                duration=duration,
                failed_tests=result_data.get('failed_tests', []),
                warnings=result_data.get('warnings', []),
                error=result_data.get('error')
            )
            
        except Exception as e:
            logger.exception("Error during test execution")
            return TestResult(
                success=False,
                message=f"Error during test execution: {str(e)}",
                error=str(e)
            )
        
        finally:
            self._cleanup_processes()
            if temp_dir:
                self._cleanup_temp_dir()

class SingleTestRunner(TestRunnerBase):
    """Runner for single test file with enhanced error handling"""
    
    def run(self, options: Dict[str, Any], selected_tests: Optional[List[str]], 
            reports_dir: str) -> TestResult:
        if not selected_tests:
            return TestResult(
                success=False, 
                message="No test file selected",
                error="No test file specified"
            )
        
        logger.info(f"Running single test: {selected_tests[0]}")
        temp_dir = None
        
        try:
            temp_dir = self._create_temp_dir()
            pytest_args = self._build_pytest_args(options, selected_tests, reports_dir)
            command = ["pytest"] + pytest_args
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = Path(reports_dir) / f"test_output_single_{timestamp}.txt"
            
            start_time = datetime.now()
            
            with timeout_handler(options.get('timeout', 300)):
                process = psutil.Popen(
                    command,
                    stdout=output_file.open('w', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                try:
                    process.wait(timeout=options.get('timeout', 300))
                except psutil.TimeoutExpired:
                    process.kill()
                    raise TestExecutionError("Test execution timed out")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result_data = self._handle_test_output(output_file)
            
            success = (process.returncode == 0 and 
                      result_data.get('failed', 0) == 0 and
                      result_data.get('errors', 0) == 0)
            
            return TestResult(
                success=success,
                message=f"Test {selected_tests[0]} completed successfully" if success else f"Test {selected_tests[0]} failed",
                duration=duration,
                failed_tests=result_data.get('failed_tests', []),
                warnings=result_data.get('warnings', []),
                error=result_data.get('error')
            )
            
        except Exception as e:
            logger.exception("Error during single test execution")
            return TestResult(
                success=False,
                message=f"Error during test execution: {str(e)}",
                error=str(e)
            )
        
        finally:
            self._cleanup_processes()
            if temp_dir:
                self._cleanup_temp_dir()

class UnitTestRunner(TestRunnerBase):
    """Runner for unit tests with enhanced error handling"""
    
    def run(self, options: Dict[str, Any], selected_tests: Optional[List[str]], 
            reports_dir: str) -> TestResult:
        logger.info("Running unit tests")
        temp_dir = None
        
        try:
            temp_dir = self._create_temp_dir()
            options['extra_args'] = "-m unit"
            pytest_args = self._build_pytest_args(options, selected_tests, reports_dir)
            command = ["pytest"] + pytest_args
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = Path(reports_dir) / f"test_output_unit_{timestamp}.txt"
            
            start_time = datetime.now()
            
            with timeout_handler(options.get('timeout', 300)):
                process = psutil.Popen(
                    command,
                    stdout=output_file.open('w', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                try:
                    process.wait(timeout=options.get('timeout', 300))
                except psutil.TimeoutExpired:
                    process.kill()
                    raise TestExecutionError("Unit test execution timed out")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result_data = self._handle_test_output(output_file)
            
            success = (process.returncode == 0 and 
                      result_data.get('failed', 0) == 0 and
                      result_data.get('errors', 0) == 0)
            
            return TestResult(
                success=success,
                message="Unit tests completed successfully" if success else "Unit tests failed",
                duration=duration,
                failed_tests=result_data.get('failed_tests', []),
                warnings=result_data.get('warnings', []),
                error=result_data.get('error')
            )
            
        except Exception as e:
            logger.exception("Error during unit test execution")
            return TestResult(
                success=False,
                message=f"Error during unit test execution: {str(e)}",
                error=str(e)
            )
        
        finally:
            self._cleanup_processes()
            if temp_dir:
                self._cleanup_temp_dir()

class IntegrationTestRunner(TestRunnerBase):
    """Runner for integration tests with enhanced error handling"""
    
    def run(self, options: Dict[str, Any], selected_tests: Optional[List[str]], 
            reports_dir: str) -> TestResult:
        logger.info("Running integration tests")
        temp_dir = None
        
        try:
            temp_dir = self._create_temp_dir()
            options['extra_args'] = "-m integration"
            pytest_args = self._build_pytest_args(options, selected_tests, reports_dir)
            command = ["pytest"] + pytest_args
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = Path(reports_dir) / f"test_output_integration_{timestamp}.txt"
            
            start_time = datetime.now()
            
            with timeout_handler(options.get('timeout', 300)):
                process = psutil.Popen(
                    command,
                    stdout=output_file.open('w', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                try:
                    process.wait(timeout=options.get('timeout', 300))
                except psutil.TimeoutExpired:
                    process.kill()
                    raise TestExecutionError("Integration test execution timed out")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result_data = self._handle_test_output(output_file)
            
            success = (process.returncode == 0 and 
                      result_data.get('failed', 0) == 0 and
                      result_data.get('errors', 0) == 0)
            
            return TestResult(
                success=success,
                message="Integration tests completed successfully" if success else "Integration tests failed",
                duration=duration,
                failed_tests=result_data.get('failed_tests', []),
                warnings=result_data.get('warnings', []),
                error=result_data.get('error')
            )
            
        except Exception as e:
            logger.exception("Error during integration test execution")
            return TestResult(
                success=False,
                message=f"Error during integration test execution: {str(e)}",
                error=str(e)
            )
        
        finally:
            self._cleanup_processes()
            if temp_dir:
                self._cleanup_temp_dir()

class PerformanceTestRunner(TestRunnerBase):
    """Runner for performance tests with enhanced error handling"""
    
    def run(self, options: Dict[str, Any], selected_tests: Optional[List[str]], 
            reports_dir: str) -> TestResult:
        logger.info("Running performance tests")
        temp_dir = None
        
        try:
            temp_dir = self._create_temp_dir()
            options['extra_args'] = "-m performance"
            pytest_args = self._build_pytest_args(options, selected_tests, reports_dir)
            command = ["pytest"] + pytest_args
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = Path(reports_dir) / f"test_output_performance_{timestamp}.txt"
            
            start_time = datetime.now()
            
            with timeout_handler(options.get('timeout', 300)):
                process = psutil.Popen(
                    command,
                    stdout=output_file.open('w', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                try:
                    process.wait(timeout=options.get('timeout', 300))
                except psutil.TimeoutExpired:
                    process.kill()
                    raise TestExecutionError("Performance test execution timed out")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result_data = self._handle_test_output(output_file)
            
            success = (process.returncode == 0 and 
                      result_data.get('failed', 0) == 0 and
                      result_data.get('errors', 0) == 0)
            
            return TestResult(
                success=success,
                message="Performance tests completed successfully" if success else "Performance tests failed",
                duration=duration,
                failed_tests=result_data.get('failed_tests', []),
                warnings=result_data.get('warnings', []),
                error=result_data.get('error')
            )
            
        except Exception as e:
            logger.exception("Error during performance test execution")
            return TestResult(
                success=False,
                message=f"Error during performance test execution: {str(e)}",
                error=str(e)
            )
        
        finally:
            self._cleanup_processes()
            if temp_dir:
                self._cleanup_temp_dir()

class FunctionalTestRunner(TestRunnerBase):
    """Runner for functional tests with enhanced error handling"""
    
    def run(self, options: Dict[str, Any], selected_tests: Optional[List[str]], 
            reports_dir: str) -> TestResult:
        logger.info("Running functional tests")
        temp_dir = None
        
        try:
            temp_dir = self._create_temp_dir()
            options['extra_args'] = "-m functional"
            pytest_args = self._build_pytest_args(options, selected_tests, reports_dir)
            command = ["pytest"] + pytest_args
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = Path(reports_dir) / f"test_output_functional_{timestamp}.txt"
            
            start_time = datetime.now()
            
            with timeout_handler(options.get('timeout', 300)):
                process = psutil.Popen(
                    command,
                    stdout=output_file.open('w', encoding='utf-8'),
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                try:
                    process.wait(timeout=options.get('timeout', 300))
                except psutil.TimeoutExpired:
                    process.kill()
                    raise TestExecutionError("Functional test execution timed out")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result_data = self._handle_test_output(output_file)
            
            success = (process.returncode == 0 and 
                      result_data.get('failed', 0) == 0 and
                      result_data.get('errors', 0) == 0)
            
            return TestResult(
                success=success,
                message="Functional tests completed successfully" if success else "Functional tests failed",
                duration=duration,
                failed_tests=result_data.get('failed_tests', []),
                warnings=result_data.get('warnings', []),
                error=result_data.get('error')
            )
            
        except Exception as e:
            logger.exception("Error during functional test execution")
            return TestResult(
                success=False,
                message=f"Error during functional test execution: {str(e)}",
                error=str(e)
            )
        
        finally:
            self._cleanup_processes()
            if temp_dir:
                self._cleanup_temp_dir()

class TestRunnerFactory:
    """Enhanced factory for creating test runners"""
    
    @staticmethod
    def create_runner(test_type: str) -> TestRunnerBase:
        """Create appropriate test runner instance with validation"""
        runners = {
            "unit": UnitTestRunner(),
            "integration": IntegrationTestRunner(),
            "performance": PerformanceTestRunner(),
            "functional": FunctionalTestRunner(),
            "all": AllTestsRunner(),
            "single": SingleTestRunner(),
        }
        
        runner = runners.get(test_type.lower())
        if runner is None:
            raise ValueError(f"Unknown test type: {test_type}")
        
        return runner

# Error handling and utility functions
def handle_keyboard_interrupt(func):
    """Decorator for handling keyboard interrupts during test execution"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            logger.warning("Test execution interrupted by user")
            return TestResult(
                success=False,
                message="Test execution interrupted by user",
                error="KeyboardInterrupt"
            )
    return wrapper