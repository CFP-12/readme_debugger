"""Code execution and sandboxing module.

담당자: 강인후
역할: 가상 환경 생성, 코드 실행, 로그 수집, 성공/실패 판정
"""

from .result import ErrorType, ExecutionResult
from .runner import CodeRunner
from .sandbox import Sandbox
from .statistics import ExecutionStats, compute_stats

__all__ = ["CodeRunner", "ExecutionResult", "ErrorType", "Sandbox", "ExecutionStats", "compute_stats"]
