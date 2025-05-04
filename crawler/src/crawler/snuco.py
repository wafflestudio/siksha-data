import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import BreakfastSchedule, CafeteriaCorner, DinnerSchedule, LunchSchedule, MealType, Menu

from .base import BaseCrawler


class SnucoCrawler(BaseCrawler):
    """Crawler for SNUCO cafeteria."""

    base_url = "https://snuco.snu.ac.kr/foodmenu/"
    supports_date = True

    CAFETERIA_REGEX = r"^(.*?)\s*(?:\((.*?)\))?$"
    """CAFETERIA_REGEX 정규표현식 예시
    Case1: 학생회관식당 (880-5543)
      - Group1: 학생회관식당
      - Group2: 880-5543
    Case2: 75-1동 4층 푸드코트
      - Group1: 75-1동 4층 푸드코트
      - Group2: None
    """
    MENU_REGEX = r"^(?:<([^<>]+)>\s*)?(?:(?:(?![\d,]+원)([^:]+?))\s*(?::\s*)?)?([\d,]+원)?\s*$"
    """MENU_REGEX 정규표현식 예시
    Case1: <A코너>뚝배기 제육콩나물비빔밥,감자채팽이버섯전,고구마맛탕 : 6,000원
      - Group1: <A코너>
      - Group2: 뚝배기 제육콩나물비빔밥,감자채팽이버섯전,고구마맛탕
      - Group3: 6,000원
    Case2: <뷔페> 6,500원
      - Group1: <뷔페>
      - Group2: None
      - Group3: 6,500원
    Case3: <서가앤쿡>
      - Group1: <서가앤쿡>
      - Group2: None
      - Group3: None
    Case4: 순두부짬뽕 : 6,300원
      - Group1: None
      - Group2: 순두부짬뽕
      - Group3: 6,300원
    Case5: 백순대볶음
      - Group1: None
      - Group2: 백순대볶음
      - Group3: None
    Case6: < 위 메뉴외에도 다양한 메뉴가 준비되어 있습니다>
      - Group1: None
      - Group2: < 위 메뉴외에도 다양한 메뉴가 준비되어 있습니다>
      - Group3: None
    """
    NO_MEAT_INDICATOR = "(#)"
    HOUR_INDICATOR = "※"
    GROUPED_MENU_CORNERS = (
        ("자하연식당 3층", "+세미뷔페", MealType.LU),
        ("302동식당", "뷔페", MealType.LU),
        ("예술계식당", "A코너", MealType.LU),
        ("예술계식당", "B코너", MealType.LU),
        ("예술계식당", "C코너", MealType.LU),
        ("예술계식당", None, MealType.DN),
    )
    SHOULD_NOT_SPLIT_MENU_NAMES = (("예술계식당", "C코너", MealType.LU),)
    DISQUALIFIED_TEXTS = ("다양한 메뉴가 준비되어 있습니다",)

    def fetch_html(self, date: datetime | None = None) -> str:
        """Fetch HTML content from SNUCO website."""
        url = self.base_url
        if date:
            # e.g., ?date=2025-03-24
            url += f"?date={date.strftime('%Y-%m-%d')}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"Error fetching {url}: {e}") from e

    def __parse_menu(
        self,
        text: str,
        meal_type: MealType,
        cafeteria_name: str,
        cafeteria_tel: str | None = None,
    ) -> list[Menu]:
        menus = []
        cafeteria_corners = []
        cafeteria_corner = CafeteriaCorner(
            name=cafeteria_name,
            cafeteria_name=cafeteria_name,
            cafeteria_tel=cafeteria_tel,
            grouped=(cafeteria_name, None, meal_type) in self.GROUPED_MENU_CORNERS,
            price=None,
        )
        cafeteria_corners.append(cafeteria_corner)

        menus_text = text.split("\n")
        for menu_text in menus_text:
            if self.HOUR_INDICATOR in menu_text:
                if "운영시간" in menu_text:
                    cafeteria_corner.operating_hours[meal_type].open_hours = menu_text.split(
                        ":", maxsplit=1
                    )[1].strip()
                elif "혼잡시간" in menu_text:
                    cafeteria_corner.operating_hours[meal_type].rush_hours = menu_text.split(
                        ":", maxsplit=1
                    )[1].strip()
                elif "라스트" in menu_text:
                    cafeteria_corner.operating_hours[meal_type].last_order = menu_text.split(
                        ":", maxsplit=1
                    )[1].strip()
                elif "브레이크" in menu_text:
                    cafeteria_corner.operating_hours[meal_type].break_hours = menu_text.split(
                        ":", maxsplit=1
                    )[1].strip()
                elif "소진" in menu_text:
                    # 301동식당 아침메뉴 예외처리
                    cafeteria_corner.operating_hours[meal_type].open_hours = menu_text.split(
                        self.HOUR_INDICATOR
                    )[1].strip()
                else:
                    cafeteria_corner.operating_hours[meal_type].additional_info.append(menu_text)
                continue

            menu_match = re.match(self.MENU_REGEX, menu_text)
            if not menu_match:
                continue

            menu_match_groups = menu_match.groups()
            corner_name = menu_match_groups[0] if menu_match_groups[0] else None
            menu_name = menu_match_groups[1].strip() if menu_match_groups[1] else None
            menu_price = menu_match_groups[2].strip() if menu_match_groups[2] else None

            if menu_name and any(text in menu_name for text in self.DISQUALIFIED_TEXTS):
                continue

            if corner_name:
                cafeteria_corner = CafeteriaCorner(
                    name=corner_name,
                    cafeteria_name=cafeteria_name,
                    cafeteria_tel=cafeteria_tel,
                    grouped=(cafeteria_name, corner_name, meal_type) in self.GROUPED_MENU_CORNERS,
                    price=menu_price,
                )
                cafeteria_corners.append(cafeteria_corner)

            if not menu_name:
                continue

            if (
                not cafeteria_corner.grouped
                or (cafeteria_name, corner_name, meal_type) in self.SHOULD_NOT_SPLIT_MENU_NAMES
            ):
                menu = Menu(
                    name=menu_name.replace(self.NO_MEAT_INDICATOR, ""),
                    price=menu_price,
                    cafeteria_corner=cafeteria_corner,
                    vegetarian=self.NO_MEAT_INDICATOR in menu_name,
                    category=None,
                )
                menus.append(menu)
            else:
                menu_names = menu_name.split(",")
                for menu_name in menu_names:
                    menu = Menu(
                        name=menu_name.replace(self.NO_MEAT_INDICATOR, ""),
                        price=menu_price,
                        cafeteria_corner=cafeteria_corner,
                        vegetarian=self.NO_MEAT_INDICATOR in menu_name,
                        category=None,
                    )
                    menus.append(menu)

        last_cafeteria_corner = cafeteria_corners[-1]
        if last_cafeteria_corner.operating_hours:
            for cafeteria_corner in cafeteria_corners[:-1]:
                if not cafeteria_corner.operating_hours:
                    cafeteria_corner.operating_hours = last_cafeteria_corner.operating_hours
                    # 두레미담 주문식 라스터오더 예외처리
                    if last_cafeteria_corner.name == "주문식 메뉴":
                        cafeteria_corner.operating_hours[meal_type].last_order = None

        return menus

    def parse(
        self, html_content: str, date: datetime
    ) -> list[BreakfastSchedule | LunchSchedule | DinnerSchedule]:
        """
        Parse HTML content from SNUCO and return schedule data.
        """
        target_date = date.date()
        schedules = []

        soup = BeautifulSoup(html_content, "html.parser")

        menu_table_body = soup.find("table", class_="menu-table").find("tbody")

        for row in menu_table_body.find_all("tr"):
            """식당 정보"""
            cafeteria_text = row.find("td", class_="title").text.strip()
            cafeteria_match_groups = re.match(self.CAFETERIA_REGEX, cafeteria_text).groups()
            cafeteria_name = cafeteria_match_groups[0]
            cafeteria_tel = cafeteria_match_groups[1] if cafeteria_match_groups[1] else None

            """아침 메뉴"""
            breakfast_text = row.find("td", class_="breakfast").text.strip()
            breakfast_menus = self.__parse_menu(
                breakfast_text, MealType.BR, cafeteria_name, cafeteria_tel
            )
            schedules.extend(
                [BreakfastSchedule(date=target_date, menu=menu) for menu in breakfast_menus]
            )

            """점심 메뉴"""
            lunch_text = row.find("td", class_="lunch").text.strip()
            lunch_menus = self.__parse_menu(lunch_text, MealType.LU, cafeteria_name, cafeteria_tel)
            schedules.extend([LunchSchedule(date=target_date, menu=menu) for menu in lunch_menus])

            """저녁 메뉴"""
            dinner_text = row.find("td", class_="dinner").text.strip()
            dinner_menus = self.__parse_menu(
                dinner_text, MealType.DN, cafeteria_name, cafeteria_tel
            )
            schedules.extend([DinnerSchedule(date=target_date, menu=menu) for menu in dinner_menus])

        return schedules
