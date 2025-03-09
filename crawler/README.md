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
```bash
# 테스트 데이터만 생성 후 테스트 실행하지 않고 종료
rye run pytest --make-data --exit-after-data

# 특정 일수만큼 데이터 생성
rye run pytest --make-data --days 14 --exit-after-data

# 특정 소스에 대해서만 데이터 생성
rye run pytest --make-data --sources snuco snuvet --exit-after-data

# 데이터 생성 후 테스트 실행
rye run pytest --make-data
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
