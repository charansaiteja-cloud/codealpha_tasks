from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"

class Finding(BaseModel):
    finding_id: str = Field(..., description="Stable unique hash for deduplication and regression tracking")
    rule_id: str = Field(..., description="Tool-specific or custom rule identifier (e.g. B108, semgrep.python.security...)")
    title: str
    description: str
    severity: Severity
    confidence: str = Field(default="HIGH", description="HIGH, MEDIUM, LOW")
    file_path: str
    start_line: int
    end_line: int
    code_snippet: Optional[str] = None
    remediation: str
    cwe_id: Optional[str] = Field(default=None, description="CWE Identifier (e.g., CWE-79, CWE-89)")
    owasp_mapping: Optional[str] = Field(default=None, description="OWASP Top 10 category (e.g. A03:2021-Injection)")
    scanner_name: str = Field(..., description="Name of the underlying engine (Bandit, Semgrep, Custom AST)")
    scanner_version: Optional[str] = None
    false_positive_status: bool = False
