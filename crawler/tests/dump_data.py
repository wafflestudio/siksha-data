import os
from datetime import datetime, timedelta

from models import MealType, OperatingHours
from src.categorizer import MenuCategorizer
from src.normalizer import MenuNormalizer
from src.registry import CrawlerRegistry
from tests.make_data import DataMaker


class DataDumper:
    CAFETERIA_CORNER_FIELDS = (
        "Cafeteria Name",
        "Corner Name",
        "Cafeteria Tel",
        "Grouped",
        "Price",
        "Operating Hours",
        "Additional Info",
    )
    MENU_FIELDS = (
        "Menu Name",
        "Cafeteria Corner",
        "Canonical Name",
        "Price",
        "Category",
        "Vegetarian",
    )

    @classmethod
    def dump_menu_data(cls, days=0, sources: list[str] | None = None):
        """메뉴 데이터를 markdown 형식으로 출력합니다."""
        raw_html_dir = os.path.join(os.path.dirname(__file__), "back_test_data", "raw_html")
        target_date = datetime.now() - timedelta(days=days)

        if sources is None:
            sources = list(CrawlerRegistry._crawlers.keys())

        normalizer = MenuNormalizer()
        categorizer = MenuCategorizer()

        print()
        print(f"# {target_date.strftime('%Y년 %m월 %d일')} 메뉴\n")

        for source in sources:
            crawler_class = CrawlerRegistry.get_crawler(source)
            crawler = crawler_class()
            html_files = DataMaker.get_html_files(raw_html_dir, source)

            # 정확한 날짜의 HTML 파일 찾기
            target_file = None
            for file, date in html_files:
                if date.date() == target_date.date():
                    target_file = (file, date)
                    break
                elif source == "snuvet" and (date.date() - target_date.date()).days % 7 == 0:
                    target_file = (file, date)
                    break

            if target_file:
                file, date = target_file
                file_path = os.path.join(raw_html_dir, file)
                html_content = None

                with open(file_path, encoding="utf-8") as f:
                    html_content = f.read()

                schedules = crawler.parse(html_content, date)

                print(f"## {source.capitalize()}\n")
                print("### 식당 정보\n")
                print("|".join(cls.CAFETERIA_CORNER_FIELDS))
                print("|".join(["---"] * len(cls.CAFETERIA_CORNER_FIELDS)))

                # CafeteriaCorner 객체를 직접 set에 저장
                cafeteria_corners = set()
                for schedule in schedules:
                    cafeteria_corners.add(schedule.menu.cafeteria_corner)

                for corner in cafeteria_corners:
                    print(
                        "|",
                        "|".join(
                            [
                                corner.cafeteria_name,
                                corner.name,
                                corner.cafeteria_tel or "",
                                str(corner.grouped),
                                corner.price or "",
                                corner.operating_hours.get(MealType.LU, OperatingHours()).open_hours
                                or "",
                                ", ".join(
                                    corner.operating_hours.get(
                                        MealType.LU, OperatingHours()
                                    ).additional_info
                                ),
                            ]
                        ),
                        "|",
                    )

                print("\n### 메뉴 정보\n")
                print("|".join(cls.MENU_FIELDS))
                print("|".join(["---"] * len(cls.MENU_FIELDS)))

                for schedule in schedules:
                    menu = schedule.menu
                    canonical_name = normalizer.normalize(menu.name)
                    category = categorizer.categorize(canonical_name) if canonical_name else None
                    print(
                        "|",
                        "|".join(
                            [
                                menu.name,
                                menu.cafeteria_corner.name,
                                canonical_name or "",
                                menu.price or "",
                                category.value if category else "",
                                str(menu.vegetarian),
                            ]
                        ),
                        "|",
                    )

                print()
            else:
                print(f"## {source.capitalize()}\n")
                print("해당 날짜의 메뉴 데이터가 없습니다.")
