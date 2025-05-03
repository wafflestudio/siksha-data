import glob
import os
from datetime import datetime

import pytest

from src.crawler.snuco import SnucoCrawler
from src.crawler.snudorm import SnudormCrawler
from src.crawler.snuvet import SnuvetCrawler
from tests.make_data import DataMaker


def pytest_addoption(parser):
    parser.addoption("--make-data", action="store_true", help="Generate test data")
    parser.addoption("--sources", nargs="+", help="Specific sources to generate data for")
    parser.addoption("--days", type=int, default=7, help="Number of days to generate data for")
    parser.addoption(
        "--exit-after-data",
        action="store_true",
        help="Exit after generating test data without running tests",
    )


@pytest.fixture(autouse=True)
def data_maker(request):
    if request.config.getoption("--make-data"):
        maker = DataMaker()
        maker.generate_test_data(
            days=request.config.getoption("--days"), sources=request.config.getoption("--sources")
        )
        # 데이터 생성 후 테스트 실행 여부 선택
        if request.config.getoption("--exit-after-data"):
            pytest.exit("Test data generated successfully")


def get_test_files(crawler_name: str) -> list[tuple[str, datetime]]:
    """크롤러별로 모든 테스트 데이터 파일과 해당 날짜를 반환합니다."""
    test_dir = os.path.join(os.path.dirname(__file__), "back_test_data", "raw_html")

    # 크롤러별 파일 패턴 매칭
    pattern = os.path.join(test_dir, f"{crawler_name}_*.html")
    files = glob.glob(pattern)

    if not files:
        raise FileNotFoundError(f"{crawler_name} 크롤러의 테스트 데이터 파일을 찾을 수 없습니다.")

    # 모든 파일에 대해 날짜 추출
    test_files = []
    for file_path in sorted(files):  # 파일명 순서대로 정렬
        file_name = os.path.basename(file_path)
        # .html 확장자 제거 후 날짜 부분만 추출
        date_parts = file_name.replace(".html", "").split("_")[1:]  # [YYYY, MM, DD]
        test_date = datetime(
            int(date_parts[0]),  # YYYY
            int(date_parts[1]),  # MM
            int(date_parts[2]),  # DD
        )
        test_files.append((file_name, test_date))

    return test_files


test_cases = []
for crawler_class, crawler_name in [
    (SnucoCrawler, "snuco"),
    (SnuvetCrawler, "snuvet"),
    (SnudormCrawler, "snudorm"),
]:
    # 각 크롤러별로 모든 테스트 파일에 대해 테스트 케이스 생성
    for test_file, test_date in get_test_files(crawler_name):
        test_cases.append(
            pytest.param(
                (crawler_class, crawler_name, test_file, test_date),
                id=f"{crawler_name}_{test_date.strftime('%Y%m%d')}",
            )
        )


@pytest.fixture(params=test_cases)
def crawler_test_data(request):
    """각 크롤러별 테스트 데이터를 제공하는 fixture입니다."""
    crawler_class, crawler_name, test_file, test_date = request.param

    # 테스트 데이터 파일 경로
    test_file_path = os.path.join(
        os.path.dirname(__file__), "back_test_data", "raw_html", test_file
    )

    # 테스트 데이터 읽기
    with open(test_file_path, encoding="utf-8") as f:
        html_content = f.read()

    return {
        "crawler_class": crawler_class,
        "crawler_name": crawler_name,
        "html_content": html_content,
        "test_date": test_date,
        "test_file": test_file,
    }
