# Siksha Crawler

식샤 프로젝트의 크롤러 모듈입니다.

## Getting Started

프로젝트는 rye를 사용하여 가상환경을 관리합니다. 모든 명령어를 실행하기 전에 가상환경을 활성화해야 합니다:

```bash
. .venv/bin/activate
```

## 테스트 실행하기

테스트는 pytest를 사용합니다. 다음과 같은 옵션들을 사용할 수 있습니다:

### 기본 테스트 실행
```bash
rye run pytest
```

### 테스트 데이터 생성

`--make-raw-html` 혹은 `--make-train-data` 옵션이 주어지는 경우 테스트가 실행되지 않습니다.

```bash
# raw HTML 파일 생성
rye run pytest -s --make-raw-html

# 학습 데이터 생성
rye run pytest -s --make-train-data

# raw HTML 파일과 학습 데이터 모두 생성
rye run pytest -s --make-raw-html --make-train-data

# 특정 일수만큼 raw HTML 파일 생성
rye run pytest -s --make-raw-html --days 14

# 특정 소스에 대해서만 데이터 생성
rye run pytest -s --make-raw-html --make-train-data --sources snuco snuvet

# 최근 3일의 데이터로 Parser 테스트 실행
rye run pytest -s --days 3 -k "test_parser"

# 최근 3일의 데이터로 Normalizer 테스트 실행
rye run pytest -s --days 3 -k "test_normalizer"

# 최근 3일의 데이터로 Categorizer 테스트 실행
rye run pytest -s --days 3 -k "test_categorizer"
```

## Noramlzier/Categorizer 사전 업데이트 및 모델 훈련 방법

아래 커맨드를 실행시켜 Interactive CLI로 새로운 데이터를 검수하고 `src/resources` 에 반영하도록 합니다.
커맨드를 실행시키기 전에 학습 데이터를 생성해야 합니다.

```bash
rye run pytest -s --make-train-data
rye run update-dict
```

## 크롤러 결과를 markdown으로 출력하기

복붙하기 쉽게 markdown 형식으로 하루치의 데이터만 출력해줍니다.

```bash
# 오늘 식단을 출력
rye run pytest -s --dump

# 하루 전 식단을 출력
rye run pytest -s --days 1 --dump

# 생협 식당 정보만을 출력
rye run pytest -s --days 1 --sources snuco --dump
```

## 식당 정보

- 생활협동조합(학생회관) 식당
  - URL: https://snuco.snu.ac.kr/foodmenu/
  - 날짜 파라미터 지원
  - 소스 코드에서 식별자: `snuco`
- 기숙사 식당
  - URL: https://snudorm.snu.ac.kr/foodmenu/
  - 날짜 파라미터 지원
  - 소스 코드에서 식별자: `snudorm`
- 수의대 식당
  - URL: https://vet.snu.ac.kr/금주의-식단/
  - 날짜 파라미터 미지원
  - 아침 메뉴는 없으며, 저녁은 단일 메뉴만 제공
  - 토요일, 일요일 메뉴 없음
  - 소스 코드에서 식별자: `snuvet`
