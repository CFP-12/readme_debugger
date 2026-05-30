"""실행 환경 및 테스트 엔진 단위 테스트.

담당자: 강인후
- CodeRunner, Sandbox, ExecutionResult 동작 검증
- 성공/실패 판정, 오류 유형 분류, timeout 처리 확인

기본 테스트는 use_system_python=True 로 venv 생성을 생략해 빠르게 실행한다.
실제 venv 격리가 필요한 통합 테스트는 @pytest.mark.slow 로 분리한다.
"""

import pytest

from pydoccheck.models import CodeBlock
from pydoccheck.execution import CodeRunner, ErrorType, ExecutionResult


# ------------------------------------------------------------------ #
# 헬퍼: 테스트용 CodeBlock 생성
# ------------------------------------------------------------------ #

def _block(
    content: str,
    block_id: str = "test_block_1",
    imports: list = None,
    executable: bool = True,
) -> CodeBlock:
    return CodeBlock(
        block_id=block_id,
        content=content,
        cleaned_content=content,
        language="python",
        file_path="test_doc.md",
        start_line=1,
        end_line=len(content.splitlines()),
        imports=imports or [],
        is_executable=executable,
        syntax_valid=True,
    )


@pytest.fixture(scope="module")
def runner():
    """빠른 테스트용 러너 - venv 생성 없이 현재 Python 사용."""
    return CodeRunner(timeout=10, use_system_python=True)


# ------------------------------------------------------------------ #
# 기본 실행 성공 케이스
# ------------------------------------------------------------------ #

class TestCodeRunnerSuccess:
    def test_simple_print(self, runner):
        result = runner.run(_block('print("hello")'))
        assert result.success is True
        assert result.stdout.strip() == "hello"
        assert result.exit_code == 0
        assert result.error_type == ErrorType.NONE
        assert result.error_message is None

    def test_arithmetic(self, runner):
        result = runner.run(_block("x = 2 + 3\nprint(x)"))
        assert result.success is True
        assert result.stdout.strip() == "5"

    def test_multiline_code(self, runner):
        code = "def add(a, b):\n    return a + b\nprint(add(1, 2))"
        result = runner.run(_block(code))
        assert result.success is True
        assert result.stdout.strip() == "3"

    def test_empty_output(self, runner):
        result = runner.run(_block("x = 1 + 1"))
        assert result.success is True
        assert result.stdout == ""

    def test_duration_is_recorded(self, runner):
        result = runner.run(_block("x = 42"))
        assert result.duration >= 0.0

    def test_block_id_preserved(self, runner):
        result = runner.run(_block("pass", block_id="my_block_99"))
        assert result.block_id == "my_block_99"


# ------------------------------------------------------------------ #
# 오류 유형 분류 케이스
# ------------------------------------------------------------------ #

class TestErrorClassification:
    def test_syntax_error(self, runner):
        result = runner.run(_block("def broken(:\n    pass"))
        assert result.success is False
        assert result.error_type == ErrorType.SYNTAX_ERROR

    def test_zero_division(self, runner):
        result = runner.run(_block("x = 1 / 0"))
        assert result.success is False
        assert result.error_type == ErrorType.RUNTIME_ERROR

    def test_name_error(self, runner):
        result = runner.run(_block("print(undefined_var)"))
        assert result.success is False
        assert result.error_type == ErrorType.RUNTIME_ERROR

    def test_type_error(self, runner):
        result = runner.run(_block('"hello" + 1'))
        assert result.success is False
        assert result.error_type == ErrorType.RUNTIME_ERROR

    def test_module_not_found(self, runner):
        result = runner.run(_block("import _no_such_module_xyz_abc"))
        assert result.success is False
        assert result.error_type in (ErrorType.MODULE_NOT_FOUND, ErrorType.IMPORT_ERROR)

    def test_stderr_captured(self, runner):
        result = runner.run(_block("raise ValueError('test error')"))
        assert result.success is False
        assert "ValueError" in result.stderr


# ------------------------------------------------------------------ #
# Timeout 처리
# ------------------------------------------------------------------ #

class TestTimeout:
    def test_timeout_detected(self):
        runner = CodeRunner(timeout=2, use_system_python=True)
        result = runner.run(_block("import time\ntime.sleep(60)"))
        assert result.success is False
        assert result.timed_out is True
        assert result.error_type == ErrorType.TIMEOUT
        assert result.exit_code == -1


# ------------------------------------------------------------------ #
# run_all + 비실행 블록 필터
# ------------------------------------------------------------------ #

class TestRunAll:
    def test_non_executable_blocks_skipped(self, runner):
        block = _block("# just a comment", executable=False)
        results = runner.run_all([block])
        assert results == []

    def test_run_all_returns_all_results(self, runner):
        blocks = [
            _block('print("a")', block_id="b1"),
            _block('print("b")', block_id="b2"),
            _block('print("c")', block_id="b3"),
        ]
        results = runner.run_all(blocks)
        assert len(results) == 3
        assert all(r.success for r in results)

    def test_run_all_mixed_results(self, runner):
        blocks = [
            _block("print(1)", block_id="ok"),
            _block("raise RuntimeError('boom')", block_id="fail"),
        ]
        results = runner.run_all(blocks)
        assert results[0].success is True
        assert results[1].success is False


# ------------------------------------------------------------------ #
# ExecutionResult 직렬화
# ------------------------------------------------------------------ #

class TestExecutionResultSerialization:
    def test_to_dict_keys(self, runner):
        result = runner.run(_block("print(42)"))
        d = result.to_dict()
        expected_keys = {
            "block_id", "success", "exit_code", "stdout",
            "stderr", "duration", "timed_out", "error_type", "error_message",
        }
        assert expected_keys == set(d.keys())

    def test_to_dict_types(self, runner):
        result = runner.run(_block("x = 1"))
        d = result.to_dict()
        assert isinstance(d["block_id"], str)
        assert isinstance(d["success"], bool)
        assert isinstance(d["exit_code"], int)
        assert isinstance(d["duration"], float)
        assert isinstance(d["error_type"], str)
        assert d["timed_out"] is False

    def test_error_type_is_string_in_dict(self, runner):
        result = runner.run(_block("raise ValueError('x')"))
        d = result.to_dict()
        assert isinstance(d["error_type"], str)
        assert d["error_type"] == ErrorType.RUNTIME_ERROR.value


# ------------------------------------------------------------------ #
# 통합 테스트: 실제 venv 격리 확인 (느린 테스트)
# ------------------------------------------------------------------ #

@pytest.mark.slow
class TestSandboxIsolation:
    def test_runs_in_isolated_venv(self):
        runner = CodeRunner(timeout=30)
        result = runner.run(_block("import sys\nprint(sys.executable)"))
        assert result.success is True
        # 격리된 venv의 python 경로가 사용되었는지 확인
        assert "pydoccheck_" in result.stdout or "venv" in result.stdout
