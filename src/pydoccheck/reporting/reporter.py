"""Rich UI 기반 터미널 시각화 및 Jinja2/Plotly 리포트 자동 생성기.

담당자: 조혜준
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from jinja2 import Template
from ..execution.result import ExecutionResult
from ..execution.statistics import ExecutionStats
from ..models.code_block import CodeBlock
try:
    from .visualizer import save_all_charts
except Exception:
    save_all_charts = None
import json
from datetime import datetime

console = Console()


class ReportEngine:
    """CLI 대시보드 화면 렌더링 및 완성도 높은 외부 리포트 파일 저장을 전담합니다."""

    def __init__(self, results: List[ExecutionResult], stats: ExecutionStats, file_stats: Dict[str, Any], block_map: Dict[str, CodeBlock]):
        self.results = results
        self.stats = stats
        self.file_stats = file_stats
        self.block_map = block_map

    def print_cli_summary(self) -> None:
        """종합 통계 요약 데이터를 터미널에 구조화된 표(Table) 형태로 출력합니다."""
        console.print("\n[bold chartreuse3]📊 검증 완료! 프로젝트 종합 통계 (Summary)[/bold chartreuse3]")
        
        table = Table(show_header=True, header_style="bold magenta", expand=False)
        table.add_column("항목 (Metric)", width=25)
        table.add_column("결과 (Value)", justify="right", width=20)

        table.add_row("총 실행 블록 수", f"{self.stats.total} 개")
        table.add_row("성공 (Passed)", f"[green]{self.stats.passed} 개 ({self.stats.pass_rate}%)[/green]")
        table.add_row("실패 (Failed)", f"[red]{self.stats.failed} 개 ({self.stats.fail_rate}%)[/red]")
        table.add_row("시간 초과 (Timeout)", f"[yellow]{self.stats.timed_out} 개[/yellow]")
        table.add_row("평균 소요 시간", f"{self.stats.avg_duration} 초")

        console.print(table)

    def print_cli_errors(self) -> None:
        """실패한 코드 블록의 원본 소스 위치, 에러 라인, 세부 로그를 패널 스타일로 덤프합니다."""
        failed_results = [r for r in self.results if not r.success]
        if not failed_results:
            console.print("\n[bold green]✨ 모든 문서 내 코드 스니펫이 예외 없이 깨끗하게 통과했습니다![/bold green]")
            return

        console.print("\n[bold red]❌ 실패 코드 블록 상세 내역 및 디버깅 가이드[/bold red]")
        for res in failed_results:
            orig_block = self.block_map.get(res.block_id)
            
            # 원본 파서 데이터와 교차 검증하여 실제 파일명 및 줄 번호 추적
            file_name = orig_block.file_path if orig_block else "Unknown File"
            start_line = orig_block.start_line if orig_block else 1
            code_content = orig_block.content if orig_block else "코드 원본을 불러올 수 없습니다."

            syntax = Syntax(
                code_content, 
                "python", 
                theme="monokai", 
                line_numbers=True, 
                start_line=start_line
            )
            
            panel = Panel(
                syntax, 
                title=f"[bold red]Block ID: {res.block_id} ({res.error_type.value})[/bold red]", 
                subtitle=f"[yellow]📍 위치: {file_name} (Line: {start_line}~)[/yellow]",
                border_style="red",
                expand=False
            )
            console.print(panel)
            
            # Stderr 로그 정밀 출력
            console.print(f"[bold dim white]─ Detailed Stderr Log (Duration: {res.duration}s) ───[/bold dim white]")
            console.print(f"[red]{res.stderr.strip() if res.stderr else res.error_message}[/red]")
            console.print("[bold dim white]" + "─" * 60 + "[/bold dim white]\n")

    def _generate_plotly_chart(self) -> str:
        """Plotly 라이브러리를 활용해 원형 분포 차트 HTML 코드를 빌드합니다. (미설치 대응 메커니즘 탑재)"""
        try:
            import plotly.graph_objects as go
            labels = ['Passed', 'Failed']
            values = [self.stats.passed, self.stats.failed]
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3, marker=dict(colors=['#2ecc71', '#e74c3c']))])
            fig.update_layout(title_text="Execution Success vs Failure Rate", width=450, height=320, margin=dict(t=40, b=10, l=10, r=10))
            return fig.to_html(full_html=False, include_plotlyjs='cdn')
        except ImportError:
            return "<div style='color:#e74c3c; font-weight:bold; padding:20px; border:1px dashed #e74c3c; border-radius:5px;'>⚠️ Plotly 라이브러리가 로컬 환경에 없어 시각화 그래픽 데이터가 제외되었습니다.</div>"

    def generate_markdown_report(self, output_path: Path) -> None:
        """Jinja2 템플릿을 사용하여 마크다운 리포트 문서를 파일로 내보냅니다."""
        md_template_str = """# 🔍 PyDocCheck 검증 결과 리포트

## 📊 1. 종합 요약 (Summary)
| 항목 (Metric) | 결과 (Value) |
| :--- | :--- |
| **총 실행 블록 수 (Total)** | {{ stats.total }} 개 |
| **성공 (Passed)** | {{ stats.passed }} 개 ({{ stats.pass_rate }}%) |
| **실패 (Failed)** | {{ stats.failed }} 개 ({{ stats.fail_rate }}%) |
| **시간 초과 (Timed Out)** | {{ stats.timed_out }} 개 |
| **평균 실행 시간 (Avg Duration)** | {{ stats.avg_duration }} 초 |

---

## ⚠️ 2. 에러 유형별 통계 (Error Distribution)
| 에러 유형 (Error Type) | 발생 건수 (Counts) |
| :--- | :--- |
{% for err, count in stats.error_counts.items() %}| **{{ err }}** | {{ count }} 건 |
{% else %}| - | 발생한 에러 없음 |
{% endfor %}

---

## ❌ 3. 실패 코드 블록 상세 로그 (Failed Blocks)
{% for result in results %}{% if not result.success %}### 🔴 Block ID: `{{ result.block_id }}`
* **오류 분류:** `{{ result.error_type.value }}`
* **실행 시간:** `{{ result.duration }} 초`

#### 💻 Stderr 상세 내용:
```stderr
{{ result.stderr if result.stderr else result.error_message }}
```
{% endif %}{% endfor %}"""

        template = Template(md_template_str)
        rendered_md = template.render(stats=self.stats, results=self.results)
        output_path.write_text(rendered_md, encoding='utf-8')

    def generate_html_report(self, output_path: Path) -> None:
        """차트 레이아웃 및 파일별 지표 테이블을 종합한 독립 대시보드형 HTML 리포트를 생성합니다.

        시각화 엔진(`visualizer.save_all_charts`)이 사용 가능하면 PNG 차트를 함께 생성하여 HTML에 포함합니다.
        """
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        chart_div = self._generate_plotly_chart()

        # visualizer를 사용해 보조 차트(이미지) 생성 시도
        image_paths = {}
        if save_all_charts:
            try:
                paths = save_all_charts(self.stats, self.results, output_dir=str(output_dir), prefix="pydoccheck")
                # 템플릿에서 사용할 수 있도록 파일명(또는 상대경로)으로 변환
                image_paths = {k: os.path.basename(v) for k, v in paths.items()}
            except Exception:
                image_paths = {}

        html_template_str = """<!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>PyDocCheck Report</title>
      <style>
        body{font-family: Arial, Helvetica, sans-serif; padding:20px; color:#2c3e50}
        .summary-box{display:flex; gap:12px; margin-bottom:18px}
        .card{background:#f7f9fb;padding:12px;border-radius:6px;flex:1}
        .flex-section{display:flex; gap:20px}
        .chart-area{flex:0 0 480px}
        .file-area{flex:1}
        table{width:100%;border-collapse:collapse}
        th,td{padding:8px;border-bottom:1px solid #e6e9ee;text-align:left}
        .badge-success{color:#2ecc71}
        .badge-danger{color:#e74c3c}
        .error-log{background:#fff3f3;padding:10px;border-radius:4px;overflow:auto}
      </style>
    </head>
    <body>
    <div class="summary-box">
        <div class="card"><h3>총 검증 코드 블록</h3><p>{{ stats.total }}개</p></div>
        <div class="card"><h3>성공률 (Pass)</h3><p style="color: #2ecc71;">{{ stats.pass_rate }}%</p></div>
        <div class="card"><h3>실패율 (Fail)</h3><p style="color: #e74c3c;">{{ stats.fail_rate }}%</p></div>
        <div class="card"><h3>평균 실행 시간</h3><p>{{ stats.avg_duration }}s</p></div>
    </div>

    <div class="flex-section">
        <div class="section chart-area">{{ chart_div | safe }}
            {% if image_paths.pass_rate %}
            <div style="margin-top:8px;"><img src="{{ image_paths.pass_rate }}" alt="pass_rate" style="max-width:100%;border:1px solid #eee;padding:6px;background:#fff"></div>
            {% endif %}
        </div>
        <div class="section file-area">
            <h3>📂 문서 파일별 검증 상태 요약</h3>
            <table>
                <thead>
                    <tr>
                        <th>검증 소스 문서 파일 경로</th>
                        <th>성공률</th>
                        <th>실패 / 전체 블록 수</th>
                    </tr>
                </thead>
                <tbody>
                    {% for fname, fdata in file_stats.items() %}
                    <tr>
                        <td style="font-family: monospace; font-size:13px; color:#2c3e50;">{{ fname }}</td>
                        <td><span class="badge {% if fdata.pass_rate >= 100 %}badge-success{% else %}badge-danger{% endif %}">{{ fdata.pass_rate }}%</span></td>
                        <td><strong>{{ fdata.failed }}</strong> / {{ fdata.total }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <h2>📝 코드 스니펫 검증 상세 결과 목록</h2>
    {% for result in results %}
    <div class="section" style="margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>코드 블록 ID: <span style="font-family: monospace; color:#2980b9;">{{ result.block_id }}</span></strong>
            {% if result.success %}
                <span class="badge badge-success">SUCCESS ({{ result.duration }}s)</span>
            {% else %}
                <span class="badge badge-danger">FAILED ({{ result.error_type }})</span>
            {% endif %}
        </div>
        {% if not result.success %}
            <p style="margin: 10px 0 5px 0; font-size: 14px; color: #c0392b; font-weight:bold;">⚠️ 요약 메세지: {{ result.error_message }}</p>
            <pre class="error-log">{{ result.stderr if result.stderr else 'No stderr output caught.' }}</pre>
        {% endif %}
        </div>
        {% endfor %}
    </body>
    </html>"""

        template = Template(html_template_str)
        rendered = template.render(stats=self.stats, results=self.results, file_stats=self.file_stats, chart_div=chart_div, image_paths=image_paths)
        output_path.write_text(rendered, encoding='utf-8')


# ------------------------------------------------------------------ #
# Module-level helper functions (tests expect these names)
# ------------------------------------------------------------------ #

def generate_markdown(stats: ExecutionStats, results: List[ExecutionResult], title: str = "PyDocCheck") -> str:
    """간단한 마크다운 리포트 문자열 생성 (테스트용 포맷 친화적)."""
    lines = [f"# {title}", "", "## 요약", ""]
    lines.append(f"| 전체 블록 수 | {stats.total} |")
    lines.append(f"| 성공 | {stats.passed} |")
    lines.append(f"| 실패 | {stats.failed} |")
    lines.append("")
    lines.append("## 오류 유형 분포")
    for k, v in getattr(stats, 'error_counts', {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 실패 블록 상세")
    for r in results:
        lines.append(f"- {r.block_id}: {'OK' if r.success else 'FAILED'}")
        if not r.success:
            lines.append(f"  - stderr: {r.stderr}")
            if r.error_message:
                lines.append(f"  - message: {r.error_message}")
    return "\n".join(lines)


def generate_json(stats: ExecutionStats, results: List[ExecutionResult]) -> str:
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "statistics": stats.to_dict(),
        "results": [r.to_dict() for r in results],
    }
    return json.dumps(payload, ensure_ascii=False)


def save_markdown(stats: ExecutionStats, results: List[ExecutionResult], path: str) -> None:
    md = generate_markdown(stats, results)
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)


def save_json(stats: ExecutionStats, results: List[ExecutionResult], path: str) -> None:
    raw = generate_json(stats, results)
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)


def print_summary(stats: ExecutionStats, results: List[ExecutionResult]) -> None:
    # 간단한 요약을 표준 출력에 찍음 (테스트는 특정 키워드 존재 여부만 확인)
    print(f"성공: {stats.passed}  실패: {stats.failed}  전체: {stats.total}")
    if getattr(stats, 'error_counts', {}):
        print("오류 유형 분포:")
        for k, v in stats.error_counts.items():
            print(f"- {k}: {v}")
    

