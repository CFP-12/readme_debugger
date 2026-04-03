# PyDocCheck
## PyDocCheck (ADT: Automated Documentation Tester)
문서는 거짓말을 하지 않아야 한다.
GitHub 저장소 내 README 및 문서에 포함된 파이썬 코드 예제의 실행 가능성을 자동으로 검증하는 통합 Dev-Tool 시스템이다.
## 프로젝트 개요 (Overview)
오늘날 오픈소스 프로젝트에서 소스 코드의 업데이트 속도를 문서가 따라가지 못하는 '문서 부채(Documentation Debt)' 현상은 신규 사용자의 진입 장벽을 높이고 프로젝트의 신뢰도를 떨어뜨린다.
PyDocCheck는 사용자가 입력한 GitHub Repository URL을 기반으로 문서 내 파이썬 코드 블록을 자동으로 추출하고, 독립된 가상 환경에서 실행하여 그 결과를 리포트로 제공합니다. 이를 통해 오픈소스 메인테이너는 문서의 정합성을 손쉽게 유지할 수 있다.
## 핵심 기능 (Key Features)
 *  Repository Analyzer: GitHub API를 통해 README.md, /docs, /examples 등 코드 블록이 포함된 문서를 자동 탐색
 *  Code Extraction Engine: mistune 파서를 활용하여 문서 내 파이썬 코드 블록(```python)을 정밀하게 추출하고 인덱싱
 *  Execution Sandbox: venv를 통해 각 코드 블록을 위한 독립적인 Ephemeral 가상 환경을 생성하여 시스템 오염 없이 안전하게 테스트를 수행
 *  Analysis & Reporting Engine: 실행 로그를 분석하여 오류 유형(Syntax, Import, Runtime 등)을 분류하고, 시각화된 통계 리포트를 제공
## 기술 스택 (Tech Stack)
Core & Backend
 * Language: Python 3.10+ (Type Hinting 적용)
 * Parsing: mistune (AST 기반), re, ast
 * Isolation: venv, subprocess (Timeout & Security 제어)
Interface & Networking
 * CLI & TUI: Typer, Rich (터미널 UI 시각화)
 * API: requests / httpx (GitHub REST API v3)
 * Reporting: Jinja2 (Markdown 템플릿), Plotly (데이터 시각화)
## 시스템 아키텍처 (Pipeline)
본 시스템은 다음과 같은 8단계 파이프라인으로 동작한다.
 1. Repository Discovery: GitHub URL 기반 저장소 구조 분석
 2. Document Loading: 문서 파일 로드 및 메타데이터 생성
 3. Code Extraction: Markdown 파싱을 통한 코드 블록 추출
 4. Preprocessing: 코드 정제 및 import 기반 의존성 추출
 5. Sandbox Execution: 가상 환경 생성 및 독립 실행
 6. Log Analysis: Traceback 분석 및 오류 유형 분류
 7. Statistics: 성공률 및 오류 분포 통계 집계
 8. Reporting: 최종 리포트 및 시각화 결과 생성
## 주요 시나리오 (Use Cases)
 * Scenario A (메인테이너): 새로운 버전 릴리즈 전, 수백 개의 문서 내 예제 코드가 여전히 유효한지 전수 검사한다.
 * Scenario B (기여자): PR을 올릴 때 GitHub Actions를 통해 내가 수정한 문서의 예제 코드가 실제로 작동하는지 자동 피드백을 받는다.
 * Scenario C (의존성 해결): 코드 내 import pandas와 같은 구문을 감지하여 필요한 라이브러리를 가상 환경에 자동 설치하고 테스트한다.
 
