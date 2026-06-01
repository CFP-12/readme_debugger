""" ExecutionResult와 CodeBlock 데이터를 기반으로 파일별 통계를 분석.

담당자: 조혜준
"""

from typing import Dict, List, Any
from ..execution.result import ExecutionResult, ErrorType
from ..execution.statistics import ExecutionStats, compute_stats
from ..models.code_block import CodeBlock


class AnalysisEngine:
    """ExecutionResult 목록과 원본 CodeBlock 데이터를 교차 분석."""

    def __init__(self, results: List[ExecutionResult], block_map: Dict[str, CodeBlock]):
        self.results = results
        self.block_map = block_map
        self.global_stats: ExecutionStats = compute_stats(results)

    def analyze_by_file(self) -> Dict[str, Dict[str, Any]]:
        """실제 원본 파일 경로(file_path)별로 성공률과 에러 분포를 그룹화하여 산출합니다."""
        file_summary: Dict[str, Dict[str, Any]] = {}

        for res in self.results:
            # block_map에서 원본 코드 블록의 실제 파일 경로 획득 (매핑 실패 시 block_id 파싱 분기 방어)
            orig_block = self.block_map.get(res.block_id)
            filename = orig_block.file_path if orig_block else res.block_id.split("#")[0]

            if filename not in file_summary:
                file_summary[filename] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": {}
                }

            file_summary[filename]["total"] += 1
            if res.success:
                file_summary[filename]["passed"] += 1
            else:
                file_summary[filename]["failed"] += 1
                if res.error_type != ErrorType.NONE:
                    err_type = res.error_type.value
                    file_summary[filename]["errors"][err_type] = file_summary[filename]["errors"].get(err_type, 0) + 1

        # ZeroDivisionError 원천 차단형 성공률 계산
        for fname, data in file_summary.items():
            total = data["total"]
            data["pass_rate"] = round((data["passed"] / total) * 100, 1) if total > 0 else 0.0

        return file_summary