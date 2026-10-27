from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from app.models.findings import Finding

class BaseScanner(ABC):
    name: str = "base_scanner"
    version: str = "1.0.0"

    @abstractmethod
    def scan(self, target_dir: Path) -> List[Finding]:
        """
        Executes static analysis on the target directory and returns normalized
        findings. Scanner failures must be signalled to the caller (for example
        with ScannerError); returning an empty list is only valid for a clean,
        complete scan with no findings.
        """
        pass
