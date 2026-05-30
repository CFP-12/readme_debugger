"""Matplotlib 기반 실행 결과 시각화.

담당자: 강인후 (5주차)
ExecutionStats를 받아 성공률 파이 차트와 오류 유형 막대그래프를 생성한다.
matplotlib이 설치되지 않은 환경에서는 ImportError 없이 안전하게 실패한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..execution.statistics import ExecutionStats


def _check_matplotlib() -> None:
    """matplotlib 설치 여부를 확인한다."""
    try:
        import matplotlib  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "시각화 기능을 사용하려면 matplotlib을 설치하세요: pip install matplotlib"
        ) from e


def plot_pass_rate(
    stats: "ExecutionStats",
    output_path: Optional[str] = None,
    show: bool = False,
) -> None:
    """성공/실패 비율 파이 차트를 생성한다.

    Args:
        stats: compute_stats()로 생성한 집계 객체
        output_path: 저장할 파일 경로 (예: "report.png"). None이면 저장 안 함.
        show: True이면 화면에 즉시 표시.
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt

    if stats.total == 0:
        return

    labels = ["성공", "실패"]
    sizes = [stats.passed, stats.failed]
    colors = ["#4CAF50", "#F44336"]
    explode = (0.05, 0)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        explode=explode,
        autopct="%1.1f%%",
        startangle=90,
        textprops={"fontsize": 13},
    )
    ax.set_title(
        f"코드 블록 실행 결과  (전체: {stats.total}건)",
        fontsize=14,
        pad=16,
    )
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_error_distribution(
    stats: "ExecutionStats",
    output_path: Optional[str] = None,
    show: bool = False,
) -> None:
    """오류 유형별 발생 횟수 막대그래프를 생성한다.

    Args:
        stats: compute_stats()로 생성한 집계 객체
        output_path: 저장할 파일 경로. None이면 저장 안 함.
        show: True이면 화면에 즉시 표시.
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt

    if not stats.error_counts:
        return

    error_types = list(stats.error_counts.keys())
    counts = [stats.error_counts[e] for e in error_types]
    colors = ["#FF7043", "#FFA726", "#AB47BC", "#42A5F5", "#26A69A", "#78909C"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(
        error_types,
        counts,
        color=colors[: len(error_types)],
        edgecolor="white",
        height=0.6,
    )
    ax.bar_label(bars, fmt="%d건", padding=4, fontsize=11)
    ax.set_xlabel("발생 횟수", fontsize=12)
    ax.set_title("오류 유형 분포", fontsize=14, pad=12)
    ax.invert_yaxis()
    ax.set_xlim(0, max(counts) * 1.2)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_duration_histogram(
    results: list,
    output_path: Optional[str] = None,
    show: bool = False,
) -> None:
    """코드 블록별 실행 시간 히스토그램을 생성한다.

    Args:
        results: CodeRunner.run_all()의 반환값 (ExecutionResult 리스트)
        output_path: 저장할 파일 경로. None이면 저장 안 함.
        show: True이면 화면에 즉시 표시.
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt

    durations = [r.duration for r in results if r.duration > 0]
    if not durations:
        return

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(durations, bins=20, color="#42A5F5", edgecolor="white", alpha=0.85)
    ax.axvline(
        sum(durations) / len(durations),
        color="#E53935",
        linestyle="--",
        linewidth=1.5,
        label=f"평균 {sum(durations)/len(durations):.2f}s",
    )
    ax.set_xlabel("실행 시간 (초)", fontsize=12)
    ax.set_ylabel("블록 수", fontsize=12)
    ax.set_title("코드 블록 실행 시간 분포", fontsize=14, pad=12)
    ax.legend(fontsize=11)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def save_all_charts(
    stats: "ExecutionStats",
    results: list,
    output_dir: str = ".",
    prefix: str = "pydoccheck",
) -> dict:
    """모든 차트를 지정 디렉터리에 저장하고 경로 딕셔너리를 반환한다.

    Returns:
        {"pass_rate": "경로", "error_dist": "경로", "duration": "경로"}
    """
    import os

    os.makedirs(output_dir, exist_ok=True)
    paths = {}

    pass_path = os.path.join(output_dir, f"{prefix}_pass_rate.png")
    plot_pass_rate(stats, output_path=pass_path)
    paths["pass_rate"] = pass_path

    if stats.error_counts:
        err_path = os.path.join(output_dir, f"{prefix}_error_dist.png")
        plot_error_distribution(stats, output_path=err_path)
        paths["error_dist"] = err_path

    dur_path = os.path.join(output_dir, f"{prefix}_duration.png")
    plot_duration_histogram(results, output_path=dur_path)
    paths["duration"] = dur_path

    return paths
