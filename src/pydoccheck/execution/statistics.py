"""실행 결과 통계 집계 엔진.

담당자: 강인후 (2주차)
ExecutionResult 목록을 받아 성공률, 오류 분포, 평균 실행 시간 등을 산출한다.
조혜준 파트(reporting)의 입력 데이터로 전달된다.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from .result import ErrorType, ExecutionResult


@dataclass
class ExecutionStats:
    """실행 결과 집계 데이터.

    JSON 스키마:
    {
        "total":        int,    -- 전체 실행 블록 수
        "passed":       int,    -- 성공 블록 수
        "failed":       int,    -- 실패 블록 수
        "timed_out":    int,    -- 타임아웃 블록 수
        "pass_rate":    float,  -- 성공률 (%)
        "fail_rate":    float,  -- 실패율 (%)
        "avg_duration": float,  -- 평균 실행 시간 (초)
        "error_counts": dict    -- 오류 유형별 발생 횟수
    }
    """

    total: int = 0
    passed: int = 0
    failed: int = 0
    timed_out: int = 0
    avg_duration: float = 0.0
    error_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        """성공률 (%)."""
        if self.total == 0:
            return 0.0
        return round(self.passed / self.total * 100, 1)

    @property
    def fail_rate(self) -> float:
        """실패율 (%)."""
        if self.total == 0:
            return 0.0
        return round(self.failed / self.total * 100, 1)

    def to_dict(self) -> dict:
        """JSON-직렬화 가능한 딕셔너리로 변환."""
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "timed_out": self.timed_out,
            "pass_rate": self.pass_rate,
            "fail_rate": self.fail_rate,
            "avg_duration": self.avg_duration,
            "error_counts": self.error_counts,
        }


def compute_stats(results: List[ExecutionResult]) -> ExecutionStats:
    """ExecutionResult 목록으로부터 통계를 집계해 반환한다.

    Args:
        results: CodeRunner.run_all() 의 반환값

    Returns:
        ExecutionStats 집계 객체
    """
    if not results:
        return ExecutionStats()

    passed = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    timed_out = [r for r in results if r.timed_out]

    # 오류 유형별 카운트 (NONE 제외)
    error_counts: Dict[str, int] = {}
    for r in failed:
        key = r.error_type.value
        if r.error_type != ErrorType.NONE:
            error_counts[key] = error_counts.get(key, 0) + 1

    avg_duration = round(sum(r.duration for r in results) / len(results), 3)

    return ExecutionStats(
        total=len(results),
        passed=len(passed),
        failed=len(failed),
        timed_out=len(timed_out),
        avg_duration=avg_duration,
        error_counts=error_counts,
    )
