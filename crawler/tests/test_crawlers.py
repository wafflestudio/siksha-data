from src.categorizer import MenuCategorizer
from src.models import MealType
from src.normalizer import MenuNormalizer


def test_parser(crawler_test_data):
    """각 크롤러의 파서 기능을 테스트합니다."""
    crawler = crawler_test_data["crawler_class"]()
    crawler_name = crawler_test_data["crawler_name"]
    html_content = crawler_test_data["html_content"]
    test_date = crawler_test_data["test_date"]

    # 파서 실행
    schedules = crawler.parse(html_content, test_date)

    # 기본 검증
    assert len(schedules) > 0, f"{crawler_name} 크롤러가 메뉴 데이터를 파싱하지 않았습니다."

    # 메뉴 타입별 검증
    breakfast_schedules = [s for s in schedules if s.meal_type == MealType.BR]
    lunch_schedules = [s for s in schedules if s.meal_type == MealType.LU]
    dinner_schedules = [s for s in schedules if s.meal_type == MealType.DN]

    # 수의대 식당은 아침 메뉴를 제공하지 않음
    if crawler_name != "snuvet":
        assert len(breakfast_schedules) > 0, (
            f"{crawler_name} 크롤러가 아침 메뉴를 파싱하지 않았습니다."
        )
    assert len(lunch_schedules) > 0, f"{crawler_name} 크롤러가 점심 메뉴를 파싱하지 않았습니다."
    assert len(dinner_schedules) > 0, f"{crawler_name} 크롤러가 저녁 메뉴를 파싱하지 않았습니다."


def test_normalizer(normalizer_test_data):
    normalizer = MenuNormalizer()

    for menu_name in normalizer_test_data:
        best, score = normalizer._fuzzy_matching(menu_name)

        print(f"{menu_name} -> {best} ({score})")


def test_categorizer(categorizer_test_data):
    categorizer = MenuCategorizer()

    for menu_name in categorizer_test_data:
        category = categorizer.categorize(menu_name)

        print(f"{menu_name} -> {category}")
