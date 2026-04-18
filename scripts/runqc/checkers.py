import subprocess
import time
import re
from pathlib import Path
from typing import List
import logging
from .models import CheckResult, QualityIssue

logger = logging.getLogger(__name__)

class BaseChecker:
    def __init__(self, name: str, command: List[str], fix_command: List[str] = []):
        self.name = name
        self.command = command
        self.fix_command = fix_command
        self.files = self.get_python_files()

    def get_python_files(self) -> List[str]:
        src_files = list(Path('src').rglob('*.py'))
        test_files = list(Path('tests').rglob('*.py'))
        return [str(p) for p in src_files + test_files]

    def run(self) -> CheckResult:
        start_time = time.time()
        try:
            logger.info(f"Running {self.name} checker...")
            result = subprocess.run(
                self.command + self.files,
                capture_output=True,
                text=True,
                check=False
            )
            duration = time.time() - start_time
            success = result.returncode == 0
            issues = self.parse_output(result.stdout + result.stderr)
            affected_files = list({issue.file for issue in issues})

            if success:
                logger.info(f"{self.name} passed with no issues.")
            else:
                logger.warning(f"{self.name} found {len(issues)} issues.")

            return CheckResult(
                checker_name=self.name,
                success=success,
                output=result.stdout + result.stderr,
                error_count=len(issues),
                duration=duration,
                affected_files=affected_files,
                issues=issues
            )
        except Exception as e:
            logger.exception(f"Error running {self.name}")
            return CheckResult(
                checker_name=self.name,
                success=False,
                output=str(e),
                error_count=1,
                duration=time.time() - start_time,
                issues=[]
            )

    def fix(self) -> CheckResult:
        if not self.fix_command:
            logger.info(f"{self.name} does not support fixing issues.")
            return CheckResult(
                checker_name=self.name,
                success=False,
                output="Fixing not supported.",
                error_count=0,
                duration=0.0,
                issues=[]
            )
        start_time = time.time()
        try:
            logger.info(f"Fixing issues with {self.name}...")
            result = subprocess.run(
                self.fix_command + self.files,
                capture_output=True,
                text=True,
                check=False
            )
            duration = time.time() - start_time
            success = result.returncode == 0
            return CheckResult(
                checker_name=self.name,
                success=success,
                output=result.stdout + result.stderr,
                error_count=0,
                duration=duration,
                issues=[]
            )
        except Exception as e:
            logger.exception(f"Error fixing issues with {self.name}")
            return CheckResult(
                checker_name=self.name,
                success=False,
                output=str(e),
                error_count=1,
                duration=time.time() - start_time,
                issues=[]
            )

    def parse_output(self, output: str) -> List[QualityIssue]:
        """Parse the tool-specific output into QualityIssue instances."""
        return []

    def is_fixable(self) -> bool:
        return bool(self.fix_command)

class BlackChecker(BaseChecker):
    def __init__(self):
        super().__init__(
            name="Black",
            command=['black', '--check'],
            fix_command=['black']
        )

    def parse_output(self, output: str) -> List[QualityIssue]:
        issues = []
        for line in output.splitlines():
            if "would reformat" in line:
                file_path = Path(line.split("would reformat")[-1].strip())
                issues.append(QualityIssue(
                    file=file_path,
                    line=None,
                    column=None,
                    code="BLACK",
                    message="File needs reformatting",
                    level="WARNING",
                    source="Black",
                    fixable=True
                ))
        return issues

class Flake8Checker(BaseChecker):
    def __init__(self):
        super().__init__(name="Flake8", command=['flake8'])

    def parse_output(self, output: str) -> List[QualityIssue]:
        issues = []
        pattern = re.compile(r"^(.*?):(\d+):(\d+): ([A-Z]\d+) (.+)$")
        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                file_path = Path(match.group(1))
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                code = match.group(4)
                message = match.group(5)

                level = "ERROR" if code.startswith(('E', 'F')) else "WARNING"

                issues.append(QualityIssue(
                    file=file_path,
                    line=line_num,
                    column=col_num,
                    code=code,
                    message=message,
                    level=level,
                    source="Flake8",
                    fixable=False
                ))
        return issues

class IsortChecker(BaseChecker):
    def __init__(self):
        super().__init__(
            name="Isort",
            command=['isort', '--check-only', '--diff'],
            fix_command=['isort']
        )

    def parse_output(self, output: str) -> List[QualityIssue]:
        issues = []
        for line in output.splitlines():
            if line.startswith("ERROR: "):
                file_path = Path(line.split("ERROR: ")[-1].strip())
                issues.append(QualityIssue(
                    file=file_path,
                    line=None,
                    column=None,
                    code="ISORT",
                    message="Imports are incorrectly sorted",
                    level="ERROR",
                    source="Isort",
                    fixable=True
                ))
        return issues

class MypyChecker(BaseChecker):
    def __init__(self):
        super().__init__(
            name="Mypy",
            command=['mypy', '--ignore-missing-imports']
        )

    def parse_output(self, output: str) -> List[QualityIssue]:
        issues = []
        pattern = re.compile(r"^(.*?):(\d+): (error|note): (.+)$")
        for line in output.splitlines():
            match = pattern.match(line)
            if match:
                file_path = Path(match.group(1))
                line_num = int(match.group(2))
                level_str = match.group(3).upper()
                message = match.group(4)
                code = ''  # Mypy does not provide a code in this format

                issues.append(QualityIssue(
                    file=file_path,
                    line=line_num,
                    column=None,
                    code=code,
                    message=message,
                    level=level_str,
                    source="Mypy",
                    fixable=False
                ))
        return issues

class CheckerFactory:
    def __init__(self):
        self.checkers = [
            BlackChecker(),
            Flake8Checker(),
            IsortChecker(),
            MypyChecker()
        ]

    def get_all_checkers(self) -> List[BaseChecker]:
        return self.checkers

    def get_fixable_checkers(self) -> List[BaseChecker]:
        return [checker for checker in self.checkers if checker.is_fixable()]
