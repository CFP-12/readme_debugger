"""PyDocCheck CLI 구동 및 엔드투엔드 파이프라인 통합 제어 컨트롤러.

담당자: 조혜준 (CLI/UI), 강인후 (GitHub URL 파이프라인 연결)

사용 예시:
    # 로컬 경로
    python -m pydoccheck.main check ./docs

    # GitHub URL (정민경 파트 연동)
    python -m pydoccheck.main check https://github.com/psf/requests
    python -m pydoccheck.main check https://github.com/psf/requests --token ghp_xxx
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

# ── 팀원 전원 모듈 연결 ──────────────────────────────────────────────────── #
from .utils.helpers import find_documents, get_parser, parse_document   # 백지유
from .execution.runner import CodeRunner                                 # 강인후
from .reporting import AnalysisEngine, ReportEngine                     # 조혜준
from .repository.fetcher import fetch_file_content, fetch_repository    # 정민경
# ─────────────────────────────────────────────────────────────────────────── #

app = typer.Typer(help="PyDocCheck: 마크다운 및 RST 문서 내부 파이썬 소스코드 격리 환경 검증 도구")
console = Console()


def _is_github_url(target: str) -> bool:
    """GitHub URL 여부를 판단한다."""
    return target.startswith("https://github.com") or target.startswith("http://github.com")


def _collect_blocks_from_github(github_url: str, token: Optional[str]) -> tuple:
    """GitHub URL → DocumentInfo 목록 → 코드 블록 수집 (정민경 파트 연동)."""
    console.print(f"🌐 GitHub 저장소 문서 수집 중: [bold cyan]{github_url}[/bold cyan]\n")

    try:
        doc_list = fetch_repository(github_url, token=token)
    except PermissionError as e:
        console.print(f"[bold red]❌ {e}[/bold red]")
        raise typer.Exit(code=1)

    if not doc_list:
        console.print("[bold yellow]ℹ️ 수집된 문서 파일이 없습니다.[/bold yellow]")
        raise typer.Exit(code=0)

    console.print(f"📄 수집된 문서: [bold]{len(doc_list)}[/bold]개\n")

    all_blocks = []
    block_map = {}

    for doc_info in doc_list:
        try:
            content = fetch_file_content(doc_info.url)
            parser = get_parser(doc_info.document_type)
            blocks = parser.parse(content, doc_info)
            for b in blocks:
                all_blocks.append(b)
                block_map[b.block_id] = b
        except ValueError:
            # 지원하지 않는 문서 형식은 조용히 넘어감
            pass
        except Exception as e:
            console.print(f"[dim red]⚠️ 파싱 오류 ({doc_info.file_path}): {e}[/dim red]")

    return all_blocks, block_map


def _collect_blocks_from_local(path: Path) -> tuple:
    """로컬 경로 → 코드 블록 수집 (기존 로직)."""
    if not path.exists():
        console.print(f"[bold red]❌ 경로를 찾을 수 없습니다: '{path}'[/bold red]")
        raise typer.Exit(code=1)

    target_files = [str(path)] if path.is_file() else find_documents(
        str(path), extensions=[".md", ".markdown", ".rst"]
    )

    if not target_files:
        console.print("[bold yellow]ℹ️ 분석 대상 문서(.md, .rst)가 없습니다.[/bold yellow]")
        raise typer.Exit(code=0)

    all_blocks = []
    block_map = {}

    for file_path in target_files:
        try:
            blocks = parse_document(file_path)
            for b in blocks:
                all_blocks.append(b)
                block_map[b.block_id] = b
        except Exception as e:
            console.print(f"[dim red]⚠️ 문서 파싱 오류 ({file_path}): {e}[/dim red]")

    return all_blocks, block_map


@app.command()
def check(
    target: str = typer.Argument(
        ...,
        help="검증할 로컬 경로(디렉터리/파일) 또는 GitHub URL (https://github.com/owner/repo)",
    ),
    report_format: str = typer.Option(
        "all", "--format", "-f",
        help="리포트 형식 (markdown | html | all | none)",
    ),
    timeout: int = typer.Option(30, "--timeout", "-t", help="블록당 실행 제한 시간 (초)"),
    use_system_python: bool = typer.Option(
        False, "--system-python",
        help="venv 생성 없이 현재 Python으로 빠르게 실행",
    ),
    token: Optional[str] = typer.Option(
        None, "--token",
        help="GitHub Personal Access Token (비공개 저장소 또는 API Rate Limit 초과 시 필요)",
    ),
):
    """로컬 경로 또는 GitHub URL의 문서 내 파이썬 코드 블록을 자동 검증합니다."""

    console.print("[bold royal_blue1]┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓[/bold royal_blue1]")
    console.print("[bold royal_blue1]┃ 🔍 PyDocCheck: 파이프라인 통합 소스코드 검증 엔진                                ┃[/bold royal_blue1]")
    console.print("[bold royal_blue1]┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛[/bold royal_blue1]")

    # ------------------------------------------------------------------ #
    # [STEP 1] 문서 수집 및 코드 블록 추출
    #   - GitHub URL → 정민경 파트(fetcher.py) 연동
    #   - 로컬 경로  → 백지유 파트(parsers) 연동
    # ------------------------------------------------------------------ #
    if _is_github_url(target):
        console.print(f"📂 분석 대상: [bold yellow]{target}[/bold yellow] (GitHub 원격 저장소)\n")
        all_blocks, block_map = _collect_blocks_from_github(target, token)
    else:
        path = Path(target)
        console.print(f"📂 분석 대상: [bold yellow]{path.resolve()}[/bold yellow] (로컬 경로)\n")
        all_blocks, block_map = _collect_blocks_from_local(path)

    executable_blocks = [
        b for b in all_blocks if b.is_executable and b.language.lower() == "python"
    ]

    if not executable_blocks:
        console.print("[bold green]☀️ 실행 가능한 파이썬 코드 블록이 없습니다. 종료합니다.[/bold green]")
        raise typer.Exit(code=0)

    console.print(f"🐍 실행 대상 코드 블록: [bold]{len(executable_blocks)}[/bold]개\n")

    # ------------------------------------------------------------------ #
    # [STEP 2] 강인후 파트: 샌드박스 격리 실행
    # ------------------------------------------------------------------ #
    runner = CodeRunner(timeout=timeout, use_system_python=use_system_python)
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Sandbox 빌드 및 코드 블록 순차 실행 중...",
            total=len(executable_blocks),
        )
        for block in executable_blocks:
            res = runner.run(block)
            results.append(res)
            progress.update(task, advance=1)

    # ------------------------------------------------------------------ #
    # [STEP 3] 조혜준 파트: 분석 및 리포트 출력
    # ------------------------------------------------------------------ #
    engine = AnalysisEngine(results, block_map)
    file_stats = engine.analyze_by_file()

    reporter = ReportEngine(results, engine.global_stats, file_stats, block_map)
    reporter.print_cli_summary()
    reporter.print_cli_errors()

    output_dir = Path("./pydoccheck_report")
    output_dir.mkdir(exist_ok=True)

    if report_format in ["markdown", "all"]:
        md_path = output_dir / "report.md"
        reporter.generate_markdown_report(md_path)
        console.print(f"[bold green]✔ Markdown 리포트 → {md_path}[/bold green]")

    if report_format in ["html", "all"]:
        html_path = output_dir / "report.html"
        reporter.generate_html_report(html_path)
        console.print(f"[bold green]✔ HTML 리포트 → {html_path}[/bold green]")

    if report_format in ["json", "all"]:
        json_path = output_dir / "report.json"
        reporter.generate_json_report(json_path)
        console.print(f"[bold green]✔ JSON 리포트 → {json_path}[/bold green]")


if __name__ == "__main__":
    app()
