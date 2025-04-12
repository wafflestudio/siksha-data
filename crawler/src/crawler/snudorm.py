import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import BreakfastSchedule, CafeteriaCorner, DinnerSchedule, LunchSchedule, MealType, Menu

from ..registry import CrawlerRegistry
from .base import BaseCrawler


@CrawlerRegistry.register("snudorm")
class SnudormCrawler(BaseCrawler):
    """Crawler for SNU dormitory cafeteria."""

    base_url = "https://snudorm.snu.ac.kr/foodmenu/"
    supports_date = True

    MENU_REGEX = r"^(?:(?:(?![\d,]+원)([^:]+?))\s*(?::\s*)?)?([\d,]+원)?\s*$"
    """MENU_REGEX 정규표현식 예시
    Case1: 짬뽕순두부찌개&메밀고기전병 : 6,000원
      - Group1: 짬뽕순두부찌개&메밀고기전병
      - Group2: 6,000원
    """
    HOUR_INDICATOR = "※"

    def fetch_html(self, date: datetime | None = None) -> str:
        """Fetch HTML content from SNU dormitory website."""
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

    def __parse_menu(self, text: str, meal_type: MealType, cafeteria_name: str) -> list[Menu]:
        menus = []
        cafeteria_corner = CafeteriaCorner(
            name=cafeteria_name,
            cafeteria_name=cafeteria_name,
            cafeteria_tel=None,
            grouped=meal_type == MealType.BR,
            price=None,
        )

        menus_text = text.split("\n")
        for menu_text in menus_text:
            line = menu_text.strip()
            if self.HOUR_INDICATOR in line:
                if "운영시간" in line:
                    cafeteria_corner.operating_hours[meal_type].open_hours = line.split(
                        ":", maxsplit=1
                    )[1].strip()
                else:
                    cafeteria_corner.operating_hours[meal_type].additional_info.append(line)

                if line.split(self.HOUR_INDICATOR)[0]:
                    # 운영시간 정보가 같은 줄에 들어오는 예외 케이스 처리
                    line = line.split(self.HOUR_INDICATOR)[0]
                else:
                    continue

            menu_match = re.match(self.MENU_REGEX, line)
            if not menu_match:
                continue

            menu_match_groups = menu_match.groups()
            menu_name = menu_match_groups[0] if menu_match_groups[0] else None
            menu_price = menu_match_groups[1] if menu_match_groups[1] else None

            if not menu_name:
                continue

            if meal_type == MealType.BR and "아워홈" in cafeteria_name:
                if menu_price:
                    cafeteria_corner.name = menu_name
                    cafeteria_corner.price = menu_price
                else:
                    menu_names = menu_name.split(",")
                    for menu_name in menu_names:
                        menu = Menu(
                            name=menu_name.strip(),
                            price=menu_price,
                            cafeteria_corner=cafeteria_corner,
                        )
                        menus.append(menu)
            else:
                menu = Menu(
                    name=menu_name,
                    price=menu_price,
                    cafeteria_corner=cafeteria_corner,
                )
                menus.append(menu)

        return menus

    def parse(
        self, html_content: str, date: datetime | None = None
    ) -> list[BreakfastSchedule | LunchSchedule | DinnerSchedule]:
        """
        Parse HTML content for the SNUDORM and return schedule data.
        """
        target_date = date.date()
        schedules = []

        soup = BeautifulSoup(html_content, "html.parser")

        menu_table_body = soup.find("table", class_="menu-table").find("tbody")

        for row in menu_table_body.find_all("tr"):
            """식당 정보"""
            cafeteria_name = row.find("td", class_="title").text.strip()

            """아침 메뉴"""
            breakfast_text = row.find("td", class_="breakfast").text.strip()
            breakfast_menus = self.__parse_menu(breakfast_text, MealType.BR, cafeteria_name)
            schedules.extend(
                [BreakfastSchedule(date=target_date, menu=menu) for menu in breakfast_menus]
            )

            """점심 메뉴"""
            lunch_text = row.find("td", class_="lunch").text.strip()
            lunch_menus = self.__parse_menu(lunch_text, MealType.LU, cafeteria_name)
            schedules.extend([LunchSchedule(date=target_date, menu=menu) for menu in lunch_menus])

            """저녁 메뉴"""
            dinner_text = row.find("td", class_="dinner").text.strip()
            dinner_menus = self.__parse_menu(dinner_text, MealType.DN, cafeteria_name)
            schedules.extend([DinnerSchedule(date=target_date, menu=menu) for menu in dinner_menus])

        return schedules
