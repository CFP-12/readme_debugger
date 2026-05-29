"""GitHub Repository Fetcher - 저장소 문서 수집 모듈

담당: 정민경
역할: GitHub URL을 입력받아 문서 파일을 수집하고 DocumentInfo 리스트로 반환
"""

import requests
from typing import List, Optional
from ..models.code_block import DocumentInfo
from ..utils.helpers import get_document_type


# 수집 대상 문서 확장자
TARGET_EXTENSIONS = [".md", ".rst", ".txt"]

# 우선 탐색 경로 (문서가 많이 있는 곳)
PRIORITY_PATHS = ["README.md", "docs/", "examples/", "tutorial/", "guide/"]


def parse_github_url(url: str) -> tuple[str, str]:
    """
    GitHub URL에서 owner, repo 이름 추출.

    Args:
        url: https://github.com/owner/repo 형태의 URL

    Returns:
        (owner, repo) 튜플
    
    Example:
        >>> parse_github_url("https://github.com/psf/requests")
        ('psf', 'requests')
    """
    # 끝에 .git 또는 / 제거
    url = url.rstrip("/").removesuffix(".git")
    parts = url.split("github.com/")[-1].split("/")

    if len(parts) < 2:
        raise ValueError(f"올바른 GitHub URL이 아닙니다: {url}")

    return parts[0], parts[1]


def fetch_file_list(owner: str, repo: str, path: str = "", token: Optional[str] = None) -> list:
    """
    GitHub API로 특정 경로의 파일 목록 조회.

    Args:
        owner: 저장소 소유자
        repo: 저장소 이름
        path: 조회할 경로 (기본값: 루트)
        token: GitHub Personal Access Token (없으면 rate limit 60회/시간)

    Returns:
        파일/폴더 정보 딕셔너리 리스트
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(api_url, headers=headers)

    if response.status_code == 404:
        return []  # 경로가 없으면 빈 리스트
    if response.status_code == 403:
        raise PermissionError("GitHub API rate limit 초과. token을 설정하세요.")
    
    response.raise_for_status()
    return response.json()


def fetch_file_content(download_url: str) -> str:
    """
    파일의 실제 내용을 다운로드.

    Args:
        download_url: GitHub raw 파일 URL

    Returns:
        파일 내용 문자열
    """
    response = requests.get(download_url)
    response.raise_for_status()
    return response.text


def collect_documents(
    owner: str,
    repo: str,
    path: str = "",
    token: Optional[str] = None,
    visited: set = None
) -> List[DocumentInfo]:
    """
    저장소 내 문서 파일을 재귀적으로 수집.

    Args:
        owner: 저장소 소유자
        repo: 저장소 이름
        path: 탐색 시작 경로
        token: GitHub Personal Access Token
        visited: 중복 방지용 방문 경로 집합

    Returns:
        DocumentInfo 리스트
    """
    if visited is None:
        visited = set()

    if path in visited:
        return []
    visited.add(path)

    items = fetch_file_list(owner, repo, path, token)
    documents = []

    for item in items:
        if item["type"] == "file":
            # 확장자 확인
            if any(item["name"].endswith(ext) for ext in TARGET_EXTENSIONS):
                doc_type = get_document_type(item["name"])
                doc_info = DocumentInfo(
                    file_path=item["path"],
                    document_type=doc_type,
                    url=item["download_url"],
                )
                documents.append(doc_info)

        elif item["type"] == "dir":
            # 하위 폴더 재귀 탐색
            sub_docs = collect_documents(owner, repo, item["path"], token, visited)
            documents.extend(sub_docs)

    return documents


def fetch_repository(github_url: str, token: Optional[str] = None) -> List[DocumentInfo]:
    """
    GitHub URL을 입력받아 문서 파일 목록을 반환하는 메인 함수.

    Args:
        github_url: https://github.com/owner/repo 형태의 URL
        token: GitHub Personal Access Token (선택)

    Returns:
        수집된 DocumentInfo 리스트

    Example:
        >>> docs = fetch_repository("https://github.com/psf/requests")
        >>> for doc in docs:
        ...     print(doc.file_path, doc.document_type)
    """
    owner, repo = parse_github_url(github_url)
    print(f"[Repository Fetcher] {owner}/{repo} 수집 시작...")

    documents = collect_documents(owner, repo, token=token)

    print(f"[Repository Fetcher] 수집 완료: 총 {len(documents)}개 문서 발견")
    return documents
