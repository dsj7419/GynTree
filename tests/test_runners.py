from abc import ABC, abstractmethod
from test_runner_utils import run_tests

class TestRunner(ABC):
    @abstractmethod
    def run(self, options, selected_tests, reports_dir):
        pass

class AllTestsRunner(TestRunner):
    def run(self, options, selected_tests, reports_dir):
        return run_tests(options, selected_tests, reports_dir)

class SingleTestRunner(TestRunner):
    def run(self, options, selected_tests, reports_dir):
        return run_tests(options, selected_tests, reports_dir)

class UnitTestRunner(TestRunner):
    def run(self, options, selected_tests, reports_dir):
        options['extra_args'] = "-m unit"
        return run_tests(options, selected_tests, reports_dir)

class IntegrationTestRunner(TestRunner):
    def run(self, options, selected_tests, reports_dir):
        options['extra_args'] = "-m 'integration'"
        return run_tests(options, selected_tests, reports_dir)

class PerformanceTestRunner(TestRunner):
    def run(self, options, selected_tests, reports_dir):
        options['extra_args'] = "-m 'performance'"
        return run_tests(options, selected_tests, reports_dir)

class FunctionalTestRunner(TestRunner):
    def run(self, options, selected_tests, reports_dir):
        options['extra_args'] = "-m 'functional'"
        return run_tests(options, selected_tests, reports_dir)

class TestRunnerFactory:
    @staticmethod
    def create_runner(test_type):
        runners = {
            "unit": UnitTestRunner(),
            "integration": IntegrationTestRunner(),
            "performance": PerformanceTestRunner(),
            "functional": FunctionalTestRunner(),
        }
        runner = runners.get(test_type.lower())
        if runner is None:
            raise ValueError(f"Unknown test type: {test_type}")
        return runner