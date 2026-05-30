"""통계 집계 및 리포트 생성 단위 테스트.

담당자: 강인후 (2주차, 4주차)
"""

import json
import os
import tempfile

import pytest

from pydoccheck.execution.result import ErrorType, ExecutionResult
from pydoccheck.execution.statistics import ExecutionStats, compute_stats
from pydoccheck.reporting.reporter import (
    generate_json,
    generate_markdown,
    print_summary,
    save_json,
    save_markdown,
)


# ------------------------------------------------------------------ #
# 헬퍼: 테스트용 ExecutionResult 생성
# ------------------------------------------------------------------ #

def _ok(block_id: str = "b1", duration: float = 0.5) -> ExecutionResult:
    return ExecutionResult(
        block_id=block_id, success=True, exit_code=0,
        stdout="ok", stderr="", duration=duration,
    )


def _fail(block_id: str = "b2", error_type: ErrorType = ErrorType.RUNTIME_ERROR,
          duration: float = 0.3) -> ExecutionResult:
    return ExecutionResult(
        block_id=block_id, success=False, exit_code=1,
        stdout="", stderr="RuntimeError: boom", duration=duration,
        error_type=error_type, error_message="boom",
    )


def _timeout(block_id: str = "b3") -> ExecutionResult:
    return ExecutionResult(
        block_id=block_id, success=False, exit_code=-1,
        stdout="", stderr="", duration=30.0,
        timed_out=True, error_type=ErrorType.TIMEOUT,
        error_message="Execution timed out",
    )


# ------------------------------------------------------------------ #
# compute_stats 테스트
# ------------------------------------------------------------------ #

class TestComputeStats:
    def test_empty_results(self):
        stats = compute_stats([])
        assert stats.total == 0
        assert stats.pass_rate == 0.0
        assert stats.fail_rate == 0.0

    def test_all_pass(self):
        results = [_ok("b1"), _ok("b2"), _ok("b3")]
        stats = compute_stats(results)
        assert stats.total == 3
        assert stats.passed == 3
        assert stats.failed == 0
        assert stats.pass_rate == 100.0
        assert stats.fail_rate == 0.0

    def test_all_fail(self):
        results = [_fail("b1"), _fail("b2")]
        stats = compute_stats(results)
        assert stats.total == 2
        assert stats.passed == 0
        assert stats.failed == 2
        assert stats.pass_rate == 0.0

    def test_mixed(self):
        results = [_ok("b1"), _ok("b2"), _fail("b3"), _timeout("b4")]
        stats = compute_stats(results)
        assert stats.total == 4
        assert stats.passed == 2
        assert stats.failed == 2
        assert stats.timed_out == 1
        assert stats.pass_rate == 50.0

    def test_error_counts(self):
        results = [
            _fail("b1", ErrorType.SYNTAX_ERROR),
            _fail("b2", ErrorType.RUNTIME_ERROR),
            _fail("b3", ErrorType.RUNTIME_ERROR),
        ]
        stats = compute_stats(results)
        assert stats.error_counts[ErrorType.RUNTIME_ERROR.value] == 2
        assert stats.error_counts[ErrorType.SYNTAX_ERROR.value] == 1

    def test_avg_duration(self):
        results = [_ok("b1", duration=1.0), _ok("b2", duration=2.0), _ok("b3", duration=3.0)]
        stats = compute_stats(results)
        assert stats.avg_duration == 2.0

    def test_to_dict_keys(self):
        stats = compute_stats([_ok()])
        d = stats.to_dict()
        expected = {"total", "passed", "failed", "timed_out",
                    "pass_rate", "fail_rate", "avg_duration", "error_counts"}
        assert set(d.keys()) == expected


# ------------------------------------------------------------------ #
# generate_markdown 테스트
# ------------------------------------------------------------------ #

class TestGenerateMarkdown:
    def setup_method(self):
        self.results = [_ok("b1"), _fail("b2"), _timeout("b3")]
        self.stats = compute_stats(self.results)

    def test_contains_title(self):
        md = generate_markdown(self.stats, self.results, title="테스트 리포트")
        assert "# 테스트 리포트" in md

    def test_contains_summary_table(self):
        md = generate_markdown(self.stats, self.results)
        assert "| 전체 블록 수 |" in md
        assert "| 성공 |" in md
        assert "| 실패 |" in md

    def test_contains_block_results(self):
        md = generate_markdown(self.stats, self.results)
        assert "b1" in md
        assert "b2" in md
        assert "b3" in md

    def test_contains_failed_detail(self):
        md = generate_markdown(self.stats, self.results)
        assert "실패 블록 상세" in md
        assert "boom" in md

    def test_contains_error_distribution(self):
        md = generate_markdown(self.stats, self.results)
        assert "오류 유형 분포" in md


# ------------------------------------------------------------------ #
# generate_json 테스트
# ------------------------------------------------------------------ #

class TestGenerateJson:
    def test_valid_json(self):
        results = [_ok(), _fail()]
        stats = compute_stats(results)
        raw = generate_json(stats, results)
        data = json.loads(raw)
        assert "statistics" in data
        assert "results" in data
        assert "generated_at" in data

    def test_results_count(self):
        results = [_ok("b1"), _ok("b2"), _fail("b3")]
        stats = compute_stats(results)
        data = json.loads(generate_json(stats, results))
        assert len(data["results"]) == 3

    def test_stats_values(self):
        results = [_ok(), _fail()]
        stats = compute_stats(results)
        data = json.loads(generate_json(stats, results))
        assert data["statistics"]["total"] == 2
        assert data["statistics"]["passed"] == 1


# ------------------------------------------------------------------ #
# 파일 저장 테스트
# ------------------------------------------------------------------ #

class TestFileSaving:
    def setup_method(self):
        self.results = [_ok("b1"), _fail("b2")]
        self.stats = compute_stats(self.results)

    def test_save_markdown(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name
        try:
            save_markdown(self.stats, self.results, path)
            assert os.path.exists(path)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert "PyDocCheck" in content
        finally:
            os.unlink(path)

    def test_save_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_json(self.stats, self.results, path)
            assert os.path.exists(path)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["statistics"]["total"] == 2
        finally:
            os.unlink(path)


# ------------------------------------------------------------------ #
# print_summary 테스트 (출력 확인)
# ------------------------------------------------------------------ #

class TestPrintSummary:
    def test_runs_without_error(self, capsys):
        results = [_ok("b1"), _fail("b2", ErrorType.SYNTAX_ERROR)]
        stats = compute_stats(results)
        print_summary(stats, results)
        captured = capsys.readouterr()
        assert "성공" in captured.out
        assert "실패" in captured.out
        assert "SyntaxError" in captured.out
