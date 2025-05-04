import os

import pytest

from src.crawler.snuco import SnucoCrawler
from src.crawler.snudorm import SnudormCrawler
from src.crawler.snuvet import SnuvetCrawler
from tests.dump_data import DataDumper
from tests.make_data import DataMaker


def pytest_addoption(parser):
    parser.addoption("--make-raw-html", action="store_true", help="Generate raw HTML files")
    parser.addoption(
        "--make-train-data", action="store_true", help="Generate training data from raw HTML files"
    )
    parser.addoption("--dump", action="store_true", help="Dump menu data in markdown format")
    parser.addoption("--sources", nargs="+", help="Specific sources to generate data for")
    parser.addoption(
        "--days", type=int, default=7, help="Number of days to generate data for or test"
    )
    parser.addoption("--go-past", type=bool, default=True, help="Go past days")


@pytest.fixture(autouse=True)
def data_maker(request):
    raw_html_dir = os.path.join(os.path.dirname(__file__), "back_test_data", "raw_html")
    training_data_dir = os.path.join(os.path.dirname(__file__), "back_test_data", "training_data")

    if request.config.getoption("--make-raw-html"):
        DataMaker.generate_raw_html(
            output_dir=raw_html_dir,
            days=request.config.getoption("--days"),
            go_past=request.config.getoption("--go-past"),
            sources=request.config.getoption("--sources"),
        )
        print("Raw HTML files generated successfully")

    if request.config.getoption("--make-train-data"):
        DataMaker.generate_training_data(
            raw_html_dir=raw_html_dir,
            output_dir=training_data_dir,
            days=request.config.getoption("--days"),
            go_past=request.config.getoption("--go-past"),
            sources=request.config.getoption("--sources"),
        )
        print("Training data generated successfully")

    if request.config.getoption("--dump"):
        days = request.config.getoption("--days")
        sources = request.config.getoption("--sources")
        DataDumper.dump_menu_data(days, sources)
        pytest.exit("Menu data dumped successfully")

    pytest.exit("Data generation completed successfully")


def _build_test_cases(config):
    cases = []
    for crawler_class, crawler_name in [
        (SnucoCrawler, "snuco"),
        (SnuvetCrawler, "snuvet"),
        (SnudormCrawler, "snudorm"),
    ]:
        # 각 크롤러별로 모든 테스트 파일에 대해 테스트 케이스 생성
        raw_html_dir = os.path.join(os.path.dirname(__file__), "back_test_data", "raw_html")
        html_files = DataMaker.get_html_files(raw_html_dir, crawler_name)

        # 날짜순으로 정렬
        html_files.sort(key=lambda x: x[1], reverse=True)

        # 현재 날짜 기준으로 offset 계산
        from datetime import datetime, timedelta

        now = datetime.now()
        days = config.getoption("--days")
        go_past = config.getoption("--go-past")

        # 기준 날짜 계산
        if go_past:
            base_date = now - timedelta(days=days)
            html_files = [(f, d) for f, d in html_files if d >= base_date]
        else:
            base_date = now + timedelta(days=days)
            html_files = [(f, d) for f, d in html_files if d <= base_date]

        for test_file, test_date in html_files:
            cases.append(
                pytest.param(
                    (crawler_class, crawler_name, test_file, test_date),
                    id=f"{crawler_name}_{test_date.strftime('%Y%m%d')}",
                )
            )
    return cases


def pytest_generate_tests(metafunc):
    """Dynamic parametrisation *before* tests are collected."""
    if (
        "crawler_test_data" in metafunc.fixturenames
        and not metafunc.config.getoption("--dump")
        and not metafunc.config.getoption("--make-train-data")
        and not metafunc.config.getoption("--make-raw-html")
    ):
        cases = _build_test_cases(metafunc.config)
        if not cases:
            pytest.skip("No test cases found")
        metafunc.parametrize("crawler_test_data", cases, indirect=True)


@pytest.fixture
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


@pytest.fixture
def normalizer_test_data(crawler_test_data):
    crawler = crawler_test_data["crawler_class"]()
    html_content = crawler_test_data["html_content"]
    test_date = crawler_test_data["test_date"]
    schedules = crawler.parse(html_content, test_date)
    menu_names = [schedule.menu.name for schedule in schedules]
    return menu_names


@pytest.fixture
def categorizer_test_data(crawler_test_data):
    crawler = crawler_test_data["crawler_class"]()
    html_content = crawler_test_data["html_content"]
    test_date = crawler_test_data["test_date"]
    schedules = crawler.parse(html_content, test_date)
    menu_names = [schedule.menu.name for schedule in schedules]
    return menu_names
