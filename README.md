# PyDocCheck

파이썬 문서를 위한 자동화된 코드 검증 도구

## 프로젝트 개요

PyDocCheck는 마크다운(`.md`)과 reStructuredText(`.rst`) 문서에 포함된 파이썬 코드 블록을 추출하고 분석하여, 문서 예시가 실제로 실행 가능한지 확인하는 도구입니다.

현재는 문서 파싱과 코드 블록 검출, 메타데이터 구축에 집중하고 있으며, 향후 샌드박스 실행 및 보고서 생성 기능을 강화할 예정입니다.

## 현재 상태 (요약)

- 문서 파싱(Markdown / RST) 및 코드 블록 메타데이터 수집
- 샌드박스(격리) 실행 엔진과 연동하여 코드 블록 실행 및 결과 집계
- 터미널 출력(리치 UI) 및 Markdown/HTML 리포트 생성 기능
- 테스트 커버리지: 프로젝트에 포함된 단위 테스트가 통과함

## 프로젝트 디렉토리 구조

```
src/pydoccheck/
├── main.py             # CLI 진입점 (Typer)
├── execution/          # 실행 엔진, 결과 모델
├── parsers/            # Markdown / RST 파서
├── reporting/          # 리포트 생성기 및 시각화
└── utils/              # 유틸리티 헬퍼
```

## 빠른 시작 (개발자용)

1. 가상환경 생성 및 활성화 (Windows 예시):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

2. 테스트 실행:

```powershell
python -m pytest -q
```

3. 샘플 문서로 CLI 실행 (개발환경에서 권장):

- Windows (명령 프롬프트):

```cmd
set PYTHONPATH=src&& .venv\Scripts\python.exe -m pydoccheck.main tests\fixtures\sample_docs -f all -t 30 --system-python
```

- POSIX (bash):

```bash
PYTHONPATH=src python -m pydoccheck.main tests/fixtures/sample_docs -f all -t 30 --system-python
```

실행 시 `pydoccheck_report/` 디렉터리가 생성되고 `report.md` 및 `report.html` 같은 결과물이 만들어집니다.

## 리포트 파일 정리

개발 중 생성된 임시 리포트 파일은 안전하게 삭제할 수 있습니다. 작업 환경에서 다음을 실행하세요:

```powershell
rmdir /S /Q pydoccheck_report
```

또는 필요한 파일만 삭제하려면:

```powershell
del pydoccheck_report\report.md
del pydoccheck_report\report.html
```

## 테스트용 샘플 문서

샘플 문서는 `tests/fixtures/sample_docs/`에 포함되어 있습니다:

- sample_simple.md
- sample_complex.md
- sample_rst.rst

## 기여 및 개발

- 로컬에서 수정 후 테스트를 통과시키고 Pull Request를 보내주세요.
- 코드 스타일과 유닛 테스트 추가를 권장합니다.

---
수정이 필요하면 어떤 부분을 더 명확히 설명할지 알려주세요.
