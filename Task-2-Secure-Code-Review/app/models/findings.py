from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class Finding(BaseModel):
    finding_id: str = Field(
        ..., description="Stable unique hash for deduplication and regression tracking"
    )
    rule_id: str = Field(
        ...,
        description="Tool-specific or custom rule identifier (for example B108).",
    )
    title: str
    description: str
    severity: Severity
    confidence: str = Field(default="HIGH", description="HIGH, MEDIUM, LOW")
    file_path: str
    start_line: int
    end_line: int
    code_snippet: str | None = None
    remediation: str
    cwe_id: str | None = Field(default=None, description="CWE Identifier (e.g., CWE-79, CWE-89)")
    owasp_mapping: str | None = Field(
        default=None, description="OWASP Top 10 category (e.g. A03:2021-Injection)"
    )
    scanner_name: str = Field(
        ..., description="Name of the underlying engine (Bandit, Semgrep, Custom AST)"
    )
    scanner_version: str | None = None
    false_positive_status: bool = False
