"""Repository analysis and document collection module.

담당자: 정민경
역할: GitHub Repository 분석 및 문서 파일 수집
"""
from .fetcher import fetch_repository

__all__ = ["fetch_repository"]