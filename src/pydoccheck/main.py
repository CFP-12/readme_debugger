"""PyDocCheck CLI 구동 및 엔드투엔드 파이프라인 통합 제어 컨트롤러.

담당자: 조혜준
- Typer 파라미터를 파싱하고, 문서 수집기(민경/지유 님 파트)와 격리 가동 엔진(인후 님 파트)을 최종 중계합니다.
"""
import os
import sys
sys.path.append(os.getcwd()) # 프로젝트 루트 경로를 PYTHONPATH에 추가하여 상대 임포트 문제 해결

from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# 팀원 전원 모듈 유기적 결합 및 임포트 선언
from .utils.helpers import find_documents, parse_document
from .execution.runner import CodeRunner

# 방금 다듬은 __init__.py를 활용한 깔끔한 패키지 임포트!
from src.pydoccheck.reporting import AnalysisEngine, ReportEngine

app = typer.Typer(help="PyDocCheck: 마크다운 및 RST 문서 내부 파이썬 소스코드 격리 환경 검증 도구")
console = Console()  # main.py 전용 독립 콘솔 객체 생성


@app.command()
def check(
    path: Path = typer.Argument(..., help="검증을 수행할 로컬 문서 디렉터리 또는 개별 파일 경로"),
    report_format: str = typer.Option("all", "--format", "-f", help="결과 보고서 추출 형식 선택 (markdown, html, all, none)"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="코드 블록별 최대 실행 제한 시간 (초)"),
    use_system_python: bool = typer.Option(False, "--system-python", help="샌드박스 가상환경을 만들지 않고 시스템 환경으로 속성 가동")
):
    """로컬 경로 내의 기술 문서 파일들을 스캔하여 내장된 파이썬 코드 블록의 정상 동작 여부를 분석합니다."""
    
    console.print("[bold royal_blue1]┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓[/bold royal_blue1]")
    console.print("[bold royal_blue1]┃ 🔍 PyDocCheck: 파이프라인 통합 소스코드 검증 엔진                                ┃[/bold royal_blue1]")
    console.print("[bold royal_blue1]┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛[/bold royal_blue1]")
    console.print(f"📂 분석 대상 타깃 경로: [bold yellow]{path.resolve()}[/bold yellow]\n")

    if not path.exists():
        console.print(f"[bold red]❌ 가동 실패: 입력한 대상 경로 '{path}' 가 파일 시스템 내에 존재하지 않습니다.[/bold red]")
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------ #
    # [STEP 1] 민경 님 & 지유 님 파트: 문서 탐색 및 코드 블록 리스트 추출
    # ------------------------------------------------------------------ #
    target_files = []
    if path.is_file():
        target_files.append(str(path))
    else:
        target_files = find_documents(str(path), extensions=['.md', '.markdown', '.rst'])

    if not target_files:
        console.print("[bold yellow]ℹ️ 스캔 결과 분석 대상 확장자(.md, .rst) 문서 파일이 존재하지 않습니다.[/bold yellow]")
        raise typer.Exit(code=0)

    all_blocks = []
    block_map = {}  # block_id 교차 조회를 위한 맵 딕셔너리
    
    for file_path in target_files:
        try:
            blocks = parse_document(file_path)
            for b in blocks:
                all_blocks.append(b)
                block_map[b.block_id] = b
        except Exception as e:
            console.print(f"[dim red]⚠️ 문서 파싱 중 오류 발생 ({file_path}): {e}[/dim red]")

    executable_blocks = [b for b in all_blocks if b.is_executable and b.language.lower() == 'python']

    if not executable_blocks:
        console.print("[bold green]☀️ 검증 대상이 되는 실행 가능 파이썬 코드 블록이 없습니다. 종료합니다.[/bold green]")
        raise typer.Exit(code=0)

    # ------------------------------------------------------------------ #
    # [STEP 2] 인후 님 파트: 샌드박스 격리 구동 엔진 작동
    # ------------------------------------------------------------------ #
    runner = CodeRunner(timeout=timeout, use_system_python=use_system_python)
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]격리 가상환경(Sandbox) 빌드 및 스니펫 순차 실행 중...", total=len(executable_blocks))
        
        for block in executable_blocks:
            res = runner.run(block)
            results.append(res)
            progress.update(task, advance=1)

    # ------------------------------------------------------------------ #
    # [STEP 3] 혜준 님 파트: 데이터 종합 교차 분석 및 보고서 바인딩 출력
    # ------------------------------------------------------------------ #
    engine = AnalysisEngine(results, block_map)
    file_stats = engine.analyze_by_file()
    
    reporter = ReportEngine(results, engine.global_stats, file_stats, block_map)
    
    # 터미널 스크린 시각화 출력
    reporter.print_cli_summary()
    reporter.print_cli_errors()

    # 결과 리포트 외부 파일 드롭 분기 처리
    output_dir = Path("./pydoccheck_report")
    output_dir.mkdir(exist_ok=True)

    if report_format in ["markdown", "all"]:
        md_path = output_dir / "report.md"
        reporter.generate_markdown_report(md_path)
        console.print(f"[bold green]✔ Markdown 리포트 파일 추출 완료 -> {md_path}[/bold green]")
        
    if report_format in ["html", "all"]:
        html_path = output_dir / "report.html"
        reporter.generate_html_report(html_path)
        console.print(f"[bold green]✔ HTML 대시보드 리포트 파일 생성 완료 -> {html_path}[/bold green]")


if __name__ == "__main__":
    app()