from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class QualityIssue:
    file: Path
    line: Optional[int]
    column: Optional[int]
    code: str
    message: str
    level: str  # e.g., "ERROR", "WARNING", "INFO"
    source: str
    fixable: bool

@dataclass
class CheckResult:
    checker_name: str
    success: bool
    output: str
    error_count: int
    duration: float
    affected_files: List[Path] = field(default_factory=list)
    issues: List[QualityIssue] = field(default_factory=list)

    def to_dict(self):
        return {
            "checker_name": self.checker_name,
            "success": self.success,
            "output": self.output,
            "error_count": self.error_count,
            "duration": self.duration,
            "affected_files": [str(p) for p in self.affected_files],
            "issues": [
                {
                    "file": str(issue.file),
                    "line": issue.line,
                    "column": issue.column,
                    "code": issue.code,
                    "message": issue.message,
                    "level": issue.level,
                    "source": issue.source,
                    "fixable": issue.fixable
                }
                for issue in self.issues
            ]
        }
