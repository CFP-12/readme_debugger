"""Result analysis and reporting module.

담당자: 조혜준 (CLI/UI 확장 예정)
       강인후 (Markdown/JSON 리포트, 시각화 구현)
역할: 오류 분석, 통계 계산, 리포트 생성, 시각화
"""

from .reporter import generate_json, generate_markdown, print_summary, save_json, save_markdown
from .visualizer import plot_error_distribution, plot_pass_rate, save_all_charts

__all__ = [
    "generate_markdown",
    "save_markdown",
    "generate_json",
    "save_json",
    "print_summary",
    "plot_pass_rate",
    "plot_error_distribution",
    "save_all_charts",
]
