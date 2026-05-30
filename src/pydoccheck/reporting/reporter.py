"""Markdown 및 CLI 기반 결과 요약 리포트 생성.

담당자: 강인후 (4주차)
ExecutionStats + ExecutionResult 목록을 받아 Markdown 텍스트와
CLI 출력(rich 없이 plain text)을 생성한다.
조혜준 파트에서 rich/CLI 인터페이스 확장 예정.
"""

import json
from datetime import datetime
from typing import List, Optional

from ..execution.result import ErrorType, ExecutionResult
from ..execution.statistics import ExecutionStats


# ------------------------------------------------------------------ #
# Markdown 리포트
# ------------------------------------------------------------------ #

def generate_markdown(
    stats: ExecutionStats,
    results: List[ExecutionResult],
    title: str = "PyDocCheck 실행 결과 리포트",
) -> str:
    """Markdown 형식의 결과 리포트 문자열을 생성한다."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 헤더
    lines += [
        f"# {title}",
        f"> 생성 일시: {now}",
        "",
    ]

    # 요약 통계
    lines += [
        "## 요약",
        "",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| 전체 블록 수 | {stats.total} |",
        f"| 성공 | {stats.passed} ({stats.pass_rate}%) |",
        f"| 실패 | {stats.failed} ({stats.fail_rate}%) |",
        f"| 타임아웃 | {stats.timed_out} |",
        f"| 평균 실행 시간 | {stats.avg_duration}s |",
        "",
    ]

    # 오류 유형 분포
    if stats.error_counts:
        lines += [
            "## 오류 유형 분포",
            "",
            "| 오류 유형 | 발생 횟수 |",
            "|-----------|-----------|",
        ]
        for err_type, count in sorted(stats.error_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {err_type} | {count} |")
        lines.append("")

    # 블록별 상세 결과
    lines += [
        "## 블록별 실행 결과",
        "",
        "| 블록 ID | 결과 | 오류 유형 | 실행 시간 |",
        "|---------|------|-----------|-----------|",
    ]
    for r in results:
        status = "✅ 성공" if r.success else "❌ 실패"
        err = r.error_type.value if not r.success else "-"
        lines.append(f"| `{r.block_id}` | {status} | {err} | {r.duration}s |")
    lines.append("")

    # 실패 블록 상세
    failed = [r for r in results if not r.success]
    if failed:
        lines += ["## 실패 블록 상세", ""]
        for r in failed:
            lines += [
                f"### `{r.block_id}`",
                f"- **오류 유형**: {r.error_type.value}",
                f"- **요약**: {r.error_message or '없음'}",
            ]
            if r.stderr.strip():
                stderr_preview = r.stderr.strip()[:500]
                lines += [
                    "```",
                    stderr_preview,
                    "```",
                ]
            lines.append("")

    return "\n".join(lines)


def save_markdown(
    stats: ExecutionStats,
    results: List[ExecutionResult],
    output_path: str,
    title: str = "PyDocCheck 실행 결과 리포트",
) -> None:
    """Markdown 리포트를 파일로 저장한다."""
    content = generate_markdown(stats, results, title)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# ------------------------------------------------------------------ #
# JSON 리포트
# ------------------------------------------------------------------ #

def generate_json(
    stats: ExecutionStats,
    results: List[ExecutionResult],
) -> str:
    """JSON 형식의 결과 리포트 문자열을 생성한다."""
    data = {
        "generated_at": datetime.now().isoformat(),
        "statistics": stats.to_dict(),
        "results": [r.to_dict() for r in results],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def save_json(
    stats: ExecutionStats,
    results: List[ExecutionResult],
    output_path: str,
) -> None:
    """JSON 리포트를 파일로 저장한다."""
    content = generate_json(stats, results)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


# ------------------------------------------------------------------ #
# CLI 요약 출력 (plain text, 조혜준 파트에서 rich로 확장 예정)
# ------------------------------------------------------------------ #

def print_summary(stats: ExecutionStats, results: List[ExecutionResult]) -> None:
    """터미널에 실행 결과 요약을 출력한다."""
    sep = "=" * 50
    print(sep)
    print("  PyDocCheck 실행 결과 요약")
    print(sep)
    print(f"  전체 블록  : {stats.total}")
    print(f"  성공       : {stats.passed}  ({stats.pass_rate}%)")
    print(f"  실패       : {stats.failed}  ({stats.fail_rate}%)")
    print(f"  타임아웃   : {stats.timed_out}")
    print(f"  평균 시간  : {stats.avg_duration}s")

    if stats.error_counts:
        print()
        print("  [오류 유형 분포]")
        for err_type, count in sorted(stats.error_counts.items(), key=lambda x: -x[1]):
            print(f"    {err_type:<25} : {count}건")

    failed = [r for r in results if not r.success]
    if failed:
        print()
        print("  [실패 블록]")
        for r in failed:
            msg = r.error_message or ""
            print(f"    ✗ {r.block_id}  ({r.error_type.value}) {msg}")

    print(sep)
