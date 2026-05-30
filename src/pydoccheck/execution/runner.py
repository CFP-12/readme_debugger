"""subprocess 기반 코드 실행 엔진.

담당자: 강인후
- 스니펫별 임시 파일 생성 후 subprocess로 실행
- stdout/stderr/exit_code/duration 수집
- 오류 유형 자동 분류 (ErrorType)
- 성공/실패 판정
"""

import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

from ..models.code_block import CodeBlock
from .result import ErrorType, ExecutionResult
from .sandbox import Sandbox


# ------------------------------------------------------------------ #
# stdlib 모듈 집합 (pip 설치 대상에서 제외)
# ------------------------------------------------------------------ #
_STDLIB: frozenset = frozenset({
    "abc", "ast", "asyncio", "builtins", "calendar", "collections",
    "contextlib", "copy", "csv", "dataclasses", "datetime", "decimal",
    "difflib", "enum", "errno", "functools", "glob", "gzip", "hashlib",
    "html", "http", "inspect", "io", "itertools", "json", "logging",
    "math", "operator", "os", "pathlib", "pickle", "platform", "pprint",
    "queue", "random", "re", "shutil", "signal", "socket", "sqlite3",
    "statistics", "string", "struct", "subprocess", "sys", "tempfile",
    "textwrap", "threading", "time", "traceback", "types", "typing",
    "unittest", "urllib", "uuid", "warnings", "weakref", "zipfile",
})

# ------------------------------------------------------------------ #
# 오류 패턴 분류 테이블 (순서 중요: 더 구체적인 패턴이 앞에 위치)
# ------------------------------------------------------------------ #
_ERROR_PATTERNS: List[Tuple[ErrorType, str]] = [
    (ErrorType.MODULE_NOT_FOUND, r"ModuleNotFoundError:"),
    (ErrorType.IMPORT_ERROR,     r"ImportError:"),
    (ErrorType.SYNTAX_ERROR,     r"SyntaxError:"),
    (ErrorType.RUNTIME_ERROR,
     r"(?:RuntimeError|TypeError|ValueError|NameError|AttributeError|ZeroDivisionError):"),
]


def _classify_error(stderr: str, timed_out: bool) -> Tuple[ErrorType, Optional[str]]:
    """stderr 로그를 분석해 오류 유형과 요약 메시지를 반환한다."""
    if timed_out:
        return ErrorType.TIMEOUT, "Execution timed out"

    for error_type, pattern in _ERROR_PATTERNS:
        for line in stderr.splitlines():
            if re.search(pattern, line):
                return error_type, line.strip()

    if stderr.strip():
        last_line = stderr.strip().splitlines()[-1].strip()
        return ErrorType.UNKNOWN, last_line

    return ErrorType.NONE, None


def _imports_to_packages(imports: List[str]) -> List[str]:
    """import 구문 목록에서 pip 설치 대상 패키지명을 추출한다."""
    seen = {}
    for stmt in imports:
        parts = stmt.split()
        if not parts:
            continue
        if parts[0] == "import":
            name = parts[1].split(".")[0]
        elif parts[0] == "from" and len(parts) >= 2:
            name = parts[1].split(".")[0]
        else:
            continue
        if name and name not in _STDLIB and name not in seen:
            seen[name] = True
    return list(seen.keys())


# ------------------------------------------------------------------ #
# 메인 실행 엔진
# ------------------------------------------------------------------ #

class CodeRunner:
    """CodeBlock을 받아 격리 환경에서 실행하고 ExecutionResult를 반환한다.

    Args:
        timeout: 단일 코드 블록 실행 제한 시간 (초, 기본값 30)
        install_timeout: pip install 제한 시간 (초, 기본값 60)
        use_system_python: True이면 venv 생성 없이 현재 Python으로 직접 실행.
                           테스트 속도 향상용. 패키지 격리가 필요 없을 때 사용.
    """

    def __init__(
        self,
        timeout: int = 30,
        install_timeout: int = 60,
        use_system_python: bool = False,
    ):
        self.timeout = timeout
        self.install_timeout = install_timeout
        self.use_system_python = use_system_python

    def run(self, block: CodeBlock) -> ExecutionResult:
        """단일 CodeBlock을 실행하고 결과를 반환한다."""
        if self.use_system_python:
            return self._run_direct(block)
        return self._run_in_sandbox(block)

    def _run_direct(self, block: CodeBlock) -> ExecutionResult:
        """venv 없이 현재 Python 인터프리터로 직접 실행 (빠른 모드)."""
        code = block.cleaned_content or block.content
        with tempfile.TemporaryDirectory(prefix="pydoccheck_direct_") as tmp_dir:
            tmp_path = Path(tmp_dir) / "snippet.py"
            tmp_path.write_text(code, encoding="utf-8")
            return self._execute(block.block_id, sys.executable, str(tmp_path))

    def _run_in_sandbox(self, block: CodeBlock) -> ExecutionResult:
        """venv 격리 환경에서 실행 (프로덕션 모드)."""
        code = block.cleaned_content or block.content

        with Sandbox() as sandbox:
            # 1) 의존성 설치
            if block.imports:
                packages = _imports_to_packages(block.imports)
                install = sandbox.install(packages, timeout=self.install_timeout)
                if install.returncode != 0:
                    return ExecutionResult(
                        block_id=block.block_id,
                        success=False,
                        exit_code=install.returncode,
                        stdout="",
                        stderr=install.stderr,
                        duration=0.0,
                        error_type=ErrorType.INSTALL_FAILED,
                        error_message=f"패키지 설치 실패: {install.stderr[:300]}",
                    )

            # 2) 임시 파일에 코드 저장
            tmp_path = str(sandbox.base_dir / "snippet.py")
            Path(tmp_path).write_text(code, encoding="utf-8")

            return self._execute(block.block_id, sandbox.python, tmp_path)

    def _execute(self, block_id: str, python: str, script: str) -> ExecutionResult:
        """subprocess로 실행하고 stdout/stderr/exit_code/duration을 수집한다."""
        timed_out = False
        start = time.monotonic()
        try:
            proc = subprocess.run(
                [python, script],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = -1
            stdout = exc.stdout.decode(errors="replace") if exc.stdout else ""
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
        finally:
            duration = round(time.monotonic() - start, 3)

        error_type, error_message = _classify_error(stderr, timed_out)
        return ExecutionResult(
            block_id=block_id,
            success=(exit_code == 0 and not timed_out),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            timed_out=timed_out,
            error_type=error_type,
            error_message=error_message,
        )

    def run_all(self, blocks: List[CodeBlock]) -> List[ExecutionResult]:
        """실행 가능한 CodeBlock 목록을 순차적으로 실행한다."""
        return [self.run(b) for b in blocks if b.is_executable]
