"""Rich UI 기반 터미널 시각화 및 Jinja2/Plotly/JSON 리포트 자동 생성기.

담당자: 조혜준
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

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

console = Console()


class ReportEngine:
    """CLI 대시보드 화면 렌더링 및 고도화된 외부 리포트 파일(Markdown, HTML, JSON) 저장을 전담합니다."""

    def __init__(self, results: List[ExecutionResult], stats: ExecutionStats, file_stats: Dict[str, Any], block_map: Dict[str, CodeBlock]):
        self.results = results
        self.stats = stats
        self.file_stats = file_stats
        self.block_map = block_map

        self.markdown_template_str = """# 🔍 PyDocCheck: 파이썬 문서 코드 검증 보고서

> **본 보고서는 문서 내에 포함된 파이썬 코드 스니펫들을 격리 환경(Sandbox)에서 가동하여 실행 무결성을 정밀 검증한 결과입니다.**
> - **검사 일시**: {{ generated_at }} (KST)
> - **검증 엔진**: PyDocCheck Core v1.0.0

---

## 📊 1. 종합 검증 지표 (Summary)

* **총 검증 문서 개수**: {{ file_stats|length }} 개
* **추출된 총 파이썬 코드 블록**: {{ stats.total }} 개
* **성공 지표 (Pass Rate)**: 🟩 **{{ stats.pass_rate }}%** ({{ stats.passed }} / {{ stats.total }} 개)
* **실패 지표 (Fail Rate)**: 🟥 **{{ stats.fail_rate }}%** ({{ stats.failed }} / {{ stats.total }} 개)
* **시간 초과 (Timeout)**: 🟨 **{{ stats.timed_out }} 개**
* **평균 소요 시간**: {{ stats.avg_duration }} 초

---

## 🗂️ 2. 문서 파일별 상세 통계 (File Statistics)

| 📄 검증 대상 문서 경로 | 📝 총 블록 | 🟩 성공 (Pass) | 🟥 실패 (Fail) | 📈 최종 성공률 |
| :--- | :---: | :---: | :---: | :---: |
{% for file_path, fdata in file_stats.items() %}
| `{{ file_path }}` | {{ fdata.total }} | {{ fdata.passed }} | {{ fdata.failed }} | **{{ fdata.pass_rate }}%** |
{% endfor %}

---

## ❌ 3. 실패한 코드 블록 분석 및 추천 수정 제안 (Detailed Analysis & Action Items)

실패율을 기록한 코드 블록들을 원인 분석하고, 에러 유형별로 즉시 복사-붙여넣기가 가능한 수준의 **AI 제안 솔루션**을 동적으로 매핑합니다.

{% set failed_exists = false %}
{% for res in results %}
{% if not res.success %}
{% set failed_exists = true %}
### 📌 [ERROR ID: {{ res.block_id }}] `{{ block_map[res.block_id].file_path if block_map.get(res.block_id) else 'Unknown File' }}`
* **위치 (Line Number)**: 원본 문서 `{{ block_map[res.block_id].start_line if block_map.get(res.block_id) else 1 }}`번째 줄 부근
* **발생 에러 유형**: `{{ res.error_type.value if hasattr(res.error_type, 'value') else res.error_type }}`
* **실행 소요 시간**: {{ res.duration }} 초

#### 💻 실패한 원본 코드 스니펫
```python
{{ block_map[res.block_id].content if block_map.get(res.block_id) else '코드 원본을 불러올 수 없습니다.' }}
```

#### 📑 샌드박스 표준 에러 로그 (Runtime Stderr)
```text
{{ res.stderr.strip() if res.stderr else res.error_message }}
```

#### 💡 추천 수정 내용 
> 해당 에러 코드를 해결하기 위한 긴급 조치 가이드라인입니다.

{% set err_str = res.error_type.value if hasattr(res.error_type, 'value') else res.error_type|string %}
{% if 'ModuleNotFoundError' in err_str %}
1. **의존성(Dependency) 누락 해결**: 가상환경 검증 중 코드 내에서 가져오려는 서드파티 패키지가 누락되었습니다. 문서 상단 혹은 프로젝트 루트의 `requirements.txt`에 해당 패키지를 명시해 주세요.
2. **패키지 명칭 오타 확인**: `import scikit-learn`이 아닌 `import sklearn`과 같이 파이썬 실제 임포트 명칭과 라이브러리명이 일치하는지 재확인하십시오.
{% elif 'ZeroDivisionError' in err_str %}
1. **분모 유효성 검증 방어 코드 삽입**: 숫자를 `0`으로 나누려는 연산이 감지되었습니다. 연산을 수행하기 전에 분모 변수가 0이 아닌지 체크하는 조건문(`if denominator != 0:`)을 선제적으로 추가하세요.
2. **예외 처리 구조화**: 런타임 크래시를 방지하기 위해 해당 연산부를 `try-except ZeroDivisionError:` 블록으로 감싸 안전하게 안전장치를 구축하세요.
{% elif 'SyntaxError' in err_str %}
1. **파이썬 문법 규격 준수**: 괄호 누락, 콜론(`:`) 생략, 혹은 잘못된 들여쓰기(Indentation)가 존재합니다. 샌드박스가 가동한 인터프리터 버전의 표준 문법 가이드를 준수해 코드를 교정하세요.
{% else %}
1. **런타임 컨텍스트 확인**: 실행 도중 예기치 못한 에러가 유발되었습니다. 표준 에러 로그의 Traceback 라인을 추적하여 값이 유효하게 초기화되었는지, 변수 범위(Scope)가 올바른지 점검하세요.
{% endif %}

---
{% endif %}
{% endfor %}
{% if not failed_exists %}
### 🎉 완벽합니다! 모든 문서 내 파이썬 코드 블록이 성공적으로 실행되었습니다.
{% endif %}

_Generated beautifully by PyDocCheck Advanced Reporter Engine Tool._
"""

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
            
            file_name = orig_block.file_path if orig_block else "Unknown File"
            start_line = orig_block.start_line if orig_block else 1
            code_content = orig_block.content if orig_block else "코드 원본을 불러올 수 없습니다."

            err_name = res.error_type.value if hasattr(res.error_type, 'value') else str(res.error_type)
            syntax = Syntax(
                code_content, 
                "python", 
                theme="monokai", 
                line_numbers=True, 
                start_line=start_line
            )
            
            panel = Panel(
                syntax, 
                title=f"[bold red]Block ID: {res.block_id} ({err_name})[/bold red]", 
                subtitle=f"[yellow]📍 위치: {file_name} (Line: {start_line}~)[/yellow]",
                border_style="red",
                expand=False
            )
            console.print(panel)
            
            console.print(f"[bold dim white]─ Detailed Stderr Log (Duration: {res.duration}s) ───[/bold dim white]")
            console.print(f"[red]{res.stderr.strip() if res.stderr else res.error_message}[/red]")
            console.print("[bold dim white]" + "─" * 60 + "[/bold dim white]\n")

    def _generate_plotly_chart(self) -> str:
        """Plotly 라이브러리를 활용해 원형 분포 차트 HTML 코드를 빌드합니다."""
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
        """실시간 실행 시간을 구하여 마크다운 파일로 빌드 및 내보냅니다."""
        # 🕒 현재 시간을 '연-월-일 시:분:초' 규격 문자열로 추출
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        template = Template(self.markdown_template_str)
        rendered_md = template.render(
            stats=self.stats, 
            results=self.results, 
            file_stats=self.file_stats, 
            block_map=self.block_map,
            generated_at=current_time_str  # 🚀 템플릿 내부 변수에 동적 바인딩
        )
        output_path.write_text(rendered_md, encoding='utf-8')

    def generate_html_report(self, output_path: Path) -> None:
        """실시간 실행 시간을 구하여 대시보드형 HTML 리포트를 생성합니다."""
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        chart_div = self._generate_plotly_chart()

        image_paths = {}
        if save_all_charts:
            try:
                paths = save_all_charts(self.stats, self.results, output_dir=str(output_dir), prefix="pydoccheck")
                image_paths = {k: os.path.basename(v) for k, v in paths.items()}
            except Exception:
                image_paths = {}

        # 🕒 HTML 리포트 상단에 노출할 현재 시간 추출
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_template_str = """<!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>PyDocCheck Advanced Dashboard</title>
      <style>
        body{font-family: 'Segoe UI', Arial, sans-serif; padding:30px; color:#2c3e50; background-color:#f8f9fa; line-height:1.6;}
        h1, h2, h3 {color: #1a365d;}
        .summary-box{display:flex; gap:16px; margin-bottom:24px}
        .card{background:#ffffff; padding:20px; border-radius:8px; flex:1; box-shadow: 0 2px 4px rgba(0,0,0,0.04); border-left: 5px solid #3182ce;}
        .card.success-card {border-left-color: #2ecc71;}
        .card.danger-card {border-left-color: #e74c3c;}
        .card h3{margin:0 0 10px 0; font-size:14px; color:#718096; text-transform:uppercase;}
        .card p{margin:0; font-size:24px; font-weight:bold;}
        .flex-section{display:flex; gap:24px; margin-bottom:30px;}
        .chart-area{flex:0 0 480px; background:#fff; padding:15px; border-radius:8px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);}
        .file-area{flex:1; background:#fff; padding:20px; border-radius:8px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);}
        table{width:100%; border-collapse:collapse; margin-top:10px;}
        th,td{padding:12px; border-bottom:1px solid #e2e8f0; text-align:left}
        th{background-color:#f7fafc; color:#4a5568; font-weight:600;}
        .badge{padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;}
        .badge-success{background-color:#ebf8ff; color:#2b6cb0;}
        .badge-danger{background-color:#fff5f5; color:#c53030;}
        .block-card {background:#fff; padding:24px; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.04); margin-bottom:20px; border:1px solid #e2e8f0;}
        .block-header {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #edf2f7; padding-bottom:12px; margin-bottom:15px;}
        pre {background:#2d3748; color:#fff; padding:15px; border-radius:6px; overflow-x:auto; font-family:Consolas, Monaco, monospace; font-size:13px;}
        .error-log{background:#fff5f5; color:#c53030; border-left:4px solid #e74c3c; padding:12px; font-family:monospace; font-size:13px; white-space:pre-wrap;}
        .recommendation-box {background:#f0fff4; border-left:4px solid #38a169; padding:15px; border-radius:4px; margin-top:15px;}
        .recommendation-title {font-weight:bold; color:#276749; margin-bottom:5px; display:flex; align-items:center; gap:6px;}
      </style>
    </head>
    <body>
    <h1>🔍 PyDocCheck 검증 무결성 대시보드</h1>
    <p style="color:#718096; font-size:14px; margin-top:-10px;">🕒 <strong>검사 일시:</strong> {{ generated_at }} (KST) | ⚙️ <strong>검증 엔진:</strong> PyDocCheck Core v1.0.0</p>
    <hr style="border:0; height:1px; background:#e2e8f0; margin-bottom:25px;">

    <div class="summary-box">
        <div class="card"><h3>총 검증 코드 블록</h3><p>{{ stats.total }} 개</p></div>
        <div class="card success-card"><h3>성공 지표 (Pass Rate)</h3><p style="color: #2ecc71;">{{ stats.pass_rate }}%</p></div>
        <div class="card danger-card"><h3>실패 지표 (Fail Rate)</h3><p style="color: #e74c3c;">{{ stats.fail_rate }}%</p></div>
        <div class="card"><h3>평균 실행 시간</h3><p>{{ stats.avg_duration }}s</p></div>
    </div>

    <div class="flex-section">
        <div class="section chart-area">
            <h3>📊 성공률 및 실패율 차트</h3>
            {{ chart_div | safe }}
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
                        <td style="font-family: monospace; font-size:13px; color:#2d3748; font-weight:500;">{{ fname }}</td>
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
    <div class="block-card">
        <div class="block-header">
            <div>
                <strong style="font-size:16px;">코드 블록 ID: <span style="font-family: monospace; color:#2b6cb0;">{{ result.block_id }}</span></strong>
                <div style="font-size:12px; color:#a0aec0; margin-top:4px;">📍 위치: {{ block_map[result.block_id].file_path if block_map.get(result.block_id) else 'Unknown' }} (Line: {{ block_map[result.block_id].start_line if block_map.get(result.block_id) else 1 }})</div>
            </div>
            {% if result.success %}
                <span class="badge badge-success" style="background-color:#e6fffa; color:#234e52;">SUCCESS ({{ result.duration }}s)</span>
            {% else %}
                <span class="badge badge-danger" style="background-color:#fff5f5; color:#742a2a;">FAILED</span>
            {% endif %}
        </div>

        <h3>💻 코드 내용 (Source Code)</h3>
        <pre><code>{{ block_map[result.block_id].content if block_map.get(result.block_id) else '# 코드를 가져올 수 없습니다.' }}</code></pre>

        {% if not result.success %}
            <h3>⚠️ 샌드박스 표준 에러 로그 (Stderr)</h3>
            <div class="error-log"><strong>[{{ result.error_type.value if hasattr(result.error_type, 'value') else result.error_type }}]</strong> {{ result.error_message }}<br><br>{{ result.stderr if result.stderr else 'No detailed stderr caught.' }}</div>
            
            <div class="recommendation-box">
                <div class="recommendation-title">💡 추천 수정 내용 (AI Recommendation)</div>
                <ul style="margin: 5px 0 0 20px; padding: 0; color: #22543d; font-size:14px;">
                {% set err_str = result.error_type.value if hasattr(result.error_type, 'value') else result.error_type|string %}
                {% if 'ModuleNotFoundError' in err_str %}
                    <li><strong>의존성 라이브러리 누락</strong>: 검증 가상환경에 해당 서드파티 모듈이 인스톨되지 않았습니다. 문서 스펙에 선행 라이브러리 가이드를 삽입하거나 호스트 패키지 목록을 보정해 주세요.</li>
                    <li><strong>임포트 식별자 체크</strong>: 패키지의 공식 PyPI 배포 명칭과 코드 상의 실제 <code>import</code> 구문 문자가 맞는지 확인하세요.</li>
                {% elif 'ZeroDivisionError' in err_str %}
                    <li><strong>분모의 Zero-Value 값 검증 누락</strong>: 런타임 상에서 값을 0으로 나누어 프로그램이 다운되었습니다. 연산 전에 분모가 0인지 필터링하는 조건 처리를 코딩해 주세요.</li>
                {% elif 'SyntaxError' in err_str %}
                    <li><strong>파이썬 문법 예외 발생</strong>: 인덴트(들여쓰기) 오염, 인자 값 매핑 기호 오류 등이 발견되었으니 파이썬 표준 규격에 맞추어 원본 문서를 가다듬어 주십시오.</li>
                {% else %}
                    <li><strong>실행 컨텍스트 분석 요망</strong>: 변수가 유효 범위를 벗어났거나 초기화되지 않은 데이터 모델을 참조 중일 수 있으니 Traceback 추적을 진행하세요.</li>
                {% endif %}
                </ul>
            </div>
        {% endif %}
    </div>
    {% endfor %}
    </body>
    </html>"""

        template = Template(html_template_str)
        rendered = template.render(
            stats=self.stats, 
            results=self.results, 
            file_stats=self.file_stats, 
            chart_div=chart_div, 
            image_paths=image_paths, 
            block_map=self.block_map,
            generated_at=current_time_str  # 🚀 HTML 상단 헤더에도 동적 주입
        )
        output_path.write_text(rendered, encoding='utf-8')

    def generate_json_report(self, output_path: Path) -> None:
        """분석 데이터, 차트 정보, 실패 블록 메타데이터를 통합 구조화하여 깨끗한 JSON 파일로 드롭합니다."""
        report_payload = {
            "meta": {
                "tool_name": "PyDocCheck Validator Engine",
                "version": "1.0.0",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 🚀 JSON 리포트 일시 보정
            },
            "global_statistics": {
                "total_blocks": self.stats.total,
                "passed_blocks": self.stats.passed,
                "failed_blocks": self.stats.failed,
                "timeout_blocks": self.stats.timed_out,
                "pass_rate_percentage": self.stats.pass_rate,
                "fail_rate_percentage": self.stats.fail_rate,
                "average_duration_seconds": self.stats.avg_duration,
                "error_counts_distribution": getattr(self.stats, 'error_counts', {})
            },
            "file_statistics": self.file_stats,
            "detailed_results": []
        }

        for res in self.results:
            orig_block = self.block_map.get(res.block_id)
            err_name = res.error_type.value if hasattr(res.error_type, 'value') else str(res.error_type)
            
            block_info = {
                "block_id": res.block_id,
                "success": res.success,
                "duration_seconds": res.duration,
                "source_metadata": {
                    "file_path": orig_block.file_path if orig_block else "Unknown File",
                    "start_line": orig_block.start_line if orig_block else 1,
                    "code_content": orig_block.content if orig_block else ""
                }
            }

            if not res.success:
                block_info["error_details"] = {
                    "error_type": err_name,
                    "error_message": res.error_message,
                    "stderr_log": res.stderr.strip() if res.stderr else ""
                }
            
            report_payload["detailed_results"].append(block_info)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, ensure_ascii=False, indent=4)

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
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 🚀 여기도 수정
        "statistics": stats.to_dict() if hasattr(stats, 'to_dict') else {},
        "results": [r.to_dict() for r in results] if hasattr(results[0], 'to_dict') else [],
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
    print(f"성공: {stats.passed}  실패: {stats.failed}  전체: {stats.total}")
    if getattr(stats, 'error_counts', {}):
        print("오류 유형 분포:")
        for k, v in stats.error_counts.items():
            print(f"- {k}: {v}")