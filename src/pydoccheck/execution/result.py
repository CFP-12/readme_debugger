"""Execution result models and error classification.

담당자: 강인후
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorType(str, Enum):
    """Classification of execution failure types."""
    NONE = "none"
    SYNTAX_ERROR = "SyntaxError"
    IMPORT_ERROR = "ImportError"
    MODULE_NOT_FOUND = "ModuleNotFoundError"
    RUNTIME_ERROR = "RuntimeError"
    TIMEOUT = "TimeoutError"
    INSTALL_FAILED = "InstallError"
    UNKNOWN = "UnknownError"


@dataclass
class ExecutionResult:
    """Result of executing a single code block inside the sandbox.

    JSON schema (표준 결과 스키마):
    {
        "block_id": str,       -- 코드 블록 고유 ID
        "success":  bool,      -- 실행 성공 여부
        "exit_code": int,      -- 프로세스 종료 코드 (0 == 정상)
        "stdout": str,         -- 표준 출력
        "stderr": str,         -- 표준 에러
        "duration": float,     -- 실행 소요 시간 (초)
        "timed_out": bool,     -- 시간 초과 여부
        "error_type": str,     -- ErrorType enum 값
        "error_message": str | null  -- 오류 요약 메시지
    }
    """

    block_id: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False
    error_type: ErrorType = ErrorType.NONE
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        """JSON-직렬화 가능한 딕셔너리로 변환."""
        return {
            "block_id": self.block_id,
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "timed_out": self.timed_out,
            "error_type": self.error_type.value,
            "error_message": self.error_message,
        }
