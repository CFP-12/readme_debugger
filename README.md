# PyDocCheck

파이썬 문서를 위한 자동화된 코드 검증 도구 (Automated Documentation Code Validator for Python)

## 프로젝트 개요

PyDocCheck는 문서(README.md, .rst 파일 등)에 포함된 파이썬 코드 예시가 실제로 실행 가능한지, 그리고 최신 상태를 유지하고 있는지 자동으로 검증하는 도구입니다.

## 현재 개발 단계: 문서 파싱 및 코드 추출

현재는 초기 개발 단계로, 다음 기능에 집중하고 있습니다:
- 마크다운(Markdown) 및 RST 문서에서 코드 블록 추출
- 추출된 코드의 전처리 및 정규화
- 코드 추적성 지표 제공을 위한 메타데이터 구축

## 프로젝트 디렉토리 구조

```
pydoccheck/
├── src/
│   └── pydoccheck/
│       ├── parsers/           # 문서 파서 (Markdown, RST)
│       ├── models/            # 데이터 모델 (CodeBlock, DocumentInfo)
│       └── utils/             # 헬퍼 유틸리티 및 공통 함수
├── tests/
│   ├── fixtures/              # 테스트 데이터 및 샘플 문서 폴더
│   └── test_*.py              # 단위 테스트 파일
├── requirements.txt           # 의존성 패키지 목록
└── README.md                  # 본 파일
```

## 시작하기

### 설치 방법

```bash
cd (설치를 원하시는 디렉토리 경로)
pip install -r requirements.txt
```

### 테스트 실행

```bash
pytest tests/test_markdown_parser.py -v
```

### 기본 사용법

```python
from pydoccheck.parsers import MarkdownParser
from pydoccheck.utils.helpers import load_document

# 문서 불러오기
content, doc_info = load_document("path/to/file.md")

# 코드 블록 파싱 및 추출
parser = MarkdownParser()
blocks = parser.parse(content, doc_info)

# 추출된 코드 정보 확인
for block in blocks:
    print(f"블록 ID {block.block_id}: 사용 언어 - {block.language}")
    print(f"코드 라인 범위: {block.start_line} ~ {block.end_line}")
    print(f"임포트된 패키지: {block.imports}")
    print(f"실행 가능 여부: {block.is_executable}")
```

## 개발 일정 (Timeline)

- **1주차**: 문서 구조 정의 및 파서 인터페이스 설계
- **2주차**: 마크다운(Markdown) 및 RST 코드 추출 엔진 구현
- **3주차**: 메타데이터 매핑 로직 추가
- **4주차**: 코드 전처리 기능 구현 (주석 제거 등)
- **5주차**: 코드 스니펫 최적화
- **6주차**: 구문(Syntax) 유효성 검증 기능 개발
- **7주차**: 코드 실행 샌드박스(Sandbox) 환경 연동
- **8주차**: 최종 검증 및 결과 보고서 생성 기능 개발

## 더미 데이터를 활용한 테스트

테스트 환경 검증을 위한 샘플 문서 파일들이 `tests/fixtures/sample_docs/` 디렉토리에 제공됩니다:
- `sample_simple.md` - 기본적인 코드 예시 문서
- `sample_complex.md` - 오류가 포함된 코드 예시 문서
- `sample_rst.rst` - reStructuredText(RST) 포맷 문서

아래 명령어를 통해 파서 구현체가 정상적으로 동작하는지 테스트할 수 있습니다:
```bash
pytest tests/ -v --tb=short
```

## 팀원 및 역할 분담

- **정민경**: 문서 분석 및 데이터 수집 (본 모듈 담당)
- **백지유**: 문서 파싱 및 코드 전처리 로직 구현
- **강인후**: 코드 실행 환경 구축 및 테스트 엔진 개발
- **조혜준**: 실행 결과 분석 및 보고서 출력 기능 구현

## 향후 진행 계획

1. 현재 구현된 파싱 기능의 무결성을 검증하기 위해 테스트 수트 실행
2. 다양한 예외 케이스(Edge cases)를 처리할 수 있도록 파서 기능 고도화
3. 코드 전처리(Preprocessing) 로직 세부 구현
4. 코드 실행 엔진(Execution engine)과의 통합 연동 작업 진행
