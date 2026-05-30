# PyDocCheck

파이썬 문서를 위한 자동화된 코드 검증 도구

## 프로젝트 개요

PyDocCheck는 마크다운(`.md`)과 reStructuredText(`.rst`) 문서에 포함된 파이썬 코드 블록을 추출하고 분석하여, 문서 예시가 실제로 실행 가능한지 확인하는 도구입니다.

현재는 문서 파싱과 코드 블록 검출, 메타데이터 구축에 집중하고 있으며, 향후 샌드박스 실행 및 보고서 생성 기능을 강화할 예정입니다.

## 현재 기능

- Markdown 및 RST 문서에서 코드 블록 추출
- 코드 블록 메타데이터 수집
- 코드 블록 실행 가능 여부 판별
- 테스트용 샘플 문서 제공

## 프로젝트 디렉토리 구조

```
PyDocCheck/
├── pyproject.toml
├── requirements.txt
├── README.md
├── src/
│   └── pydoccheck/
│       ├── __init__.py
│       ├── main.py
│       ├── execution/
│       ├── models/
│       ├── parsers/
│       ├── reporting/
│       └── utils/
└── tests/
    ├── fixtures/
    │   └── sample_docs/
    └── test_*.py
```

## 설치 방법

```bash
cd 설치하고 싶은 디렉토리 주소
python -m pip install -r requirements.txt
```

개발 환경에서는 다음과 같이 편리하게 설치할 수 있습니다:

```bash
python -m pip install -e .
```

## 테스트 실행

```bash
pytest tests/ -v --tb=short
```

특정 테스트만 실행하려면:

```bash
pytest tests/test_markdown_parser.py -v
```

## 사용 방법

### 파이썬 코드에서 사용

```python
from pydoccheck.parsers import MarkdownParser
from pydoccheck.utils.helpers import load_document

content, doc_info = load_document("tests/fixtures/sample_docs/sample_simple.md")
parser = MarkdownParser()
blocks = parser.parse(content, doc_info)

for block in blocks:
    print(f"블록 ID: {block.block_id}")
    print(f"언어: {block.language}")
    print(f"시작 줄: {block.start_line}, 종료 줄: {block.end_line}")
    print(f"임포트: {block.imports}")
    print(f"실행 가능: {block.is_executable}")
```

### CLI 실행

현재 CLI 진입점은 `src/pydoccheck/main.py`입니다. 루트 폴더에서 다음 명령을 실행하세요:

```bash
python src/pydoccheck/main.py check path/to/docs --format all --timeout 30
```

## 테스트용 샘플 문서

샘플 문서 파일들은 `tests/fixtures/sample_docs/`에 있습니다:

- `sample_simple.md`
- `sample_complex.md`
- `sample_rst.rst`

## 개발 일정

- **1주차**: 문서 구조 정의 및 파서 인터페이스 설계
- **2주차**: Markdown/RST 코드 추출 엔진 구현
- **3주차**: 메타데이터 매핑 로직 추가
- **4주차**: 코드 전처리 기능 구현
- **5주차**: 코드 스니펫 최적화
- **6주차**: 구문 유효성 검증 기능 개발
- **7주차**: 샌드박스 실행 환경 연동
- **8주차**: 보고서 생성 및 결과 출력 기능 개발

## 팀원 및 역할

- **정민경**: 문서 분석 및 데이터 수집
- **백지유**: 문서 파싱 및 코드 전처리
- **강인후**: 코드 실행 환경 및 테스트 엔진
- **조혜준**: 결과 분석 및 보고서 출력

## 향후 계획

1. 파서 기능 무결성 검증 및 테스트 커버리지 확장
2. 다양한 예외 케이스 처리 강화
3. 코드 전처리 및 정규화 로직 보완
4. 격리 실행 엔진과 통합된 검증 파이프라인 완성
