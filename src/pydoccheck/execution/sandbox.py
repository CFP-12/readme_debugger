"""Isolated virtual environment management for safe code execution.

담당자: 강인후
각 코드 블록은 독립된 venv 환경에서 실행되며, 실행 후 자동 삭제(Ephemeral)된다.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional


class Sandbox:
    """venv 기반 격리 실행 환경.

    context manager로 사용하면 __exit__ 시 환경을 자동으로 정리한다.

    사용 예시:
        with Sandbox() as sb:
            sb.install(["requests"])
            result = subprocess.run([sb.python, "script.py"], ...)
    """

    def __init__(self, base_dir: Optional[str] = None):
        self._owns_base = base_dir is None
        self._base = Path(base_dir) if base_dir else Path(tempfile.mkdtemp(prefix="pydoccheck_"))
        self._venv = self._base / "venv"

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "Sandbox":
        self.create()
        return self

    def __exit__(self, *_) -> None:
        self.cleanup()

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def base_dir(self) -> Path:
        return self._base

    @property
    def python(self) -> str:
        """venv 내부 python 실행 경로."""
        if sys.platform == "win32":
            return str(self._venv / "Scripts" / "python.exe")
        return str(self._venv / "bin" / "python")

    @property
    def pip(self) -> str:
        """venv 내부 pip 실행 경로."""
        if sys.platform == "win32":
            return str(self._venv / "Scripts" / "pip.exe")
        return str(self._venv / "bin" / "pip")

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def create(self) -> None:
        """venv를 생성한다."""
        subprocess.run(
            [sys.executable, "-m", "venv", str(self._venv)],
            check=True,
            capture_output=True,
        )

    def cleanup(self) -> None:
        """임시 디렉터리와 venv를 삭제한다."""
        if self._owns_base and self._base.exists():
            shutil.rmtree(self._base, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # Package installation
    # ------------------------------------------------------------------ #

    def install(self, packages: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """패키지를 venv에 설치하고 subprocess 결과를 반환한다."""
        if not packages:
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        return subprocess.run(
            [self.pip, "install", "--quiet", *packages],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
