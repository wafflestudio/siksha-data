from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import BreakfastSchedule, CafeteriaCorner, DinnerSchedule, LunchSchedule, MealType, Menu

from .base import BaseCrawler


class SnuvetCrawler(BaseCrawler):
    """Crawler for SNU veterinary cafeteria."""

    base_url = "https://vet.snu.ac.kr/금주의-식단/"
    supports_date = False

    def fetch_html(self, date: datetime | None = None) -> str:
        """Fetch HTML content from SNU veterinary cafeteria website."""
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"Error fetching {self.base_url}: {e}") from e

    def parse(
        self, html_content: str, date: datetime
    ) -> list[BreakfastSchedule | LunchSchedule | DinnerSchedule]:
        """
        Parse HTML content from SNU Vet site and return schedule data.
        - Typically shows a weekly table: Monday ~ Friday lunches, plus 1 dinner menu repeated.
        - No breakfast menu
        - Nothing on weekends
        """
        target_date = date.date()
        schedules = []

        soup = BeautifulSoup(html_content, "html.parser")

        # 수의대 식당은 property="og:description"인 meta tag에 식단 정보가 있음
        # 하지만 언제까지 유지될 지 모르니 활용하지 않는다
        menu_heading = soup.find("h2", string="금주의 식단")
        menu_table = menu_heading.find_next("table")
        dinner_table = menu_table.find_next("ul")

        cafeteria_corner = CafeteriaCorner(
            name="수의대 식당",
            cafeteria_name="수의대 식당",
            cafeteria_tel=None,
            grouped=False,
            price=None,
        )

        for row in menu_table.find_all("tr")[1:]:
            cells = row.find_all("td")
            date = cells[0].text.strip()
            lunch = cells[1].text.strip()

            menu = Menu(
                name=lunch,
                price=None,
                cafeteria_corner=cafeteria_corner,
                vegetarian=False,
                category=None,
            )

            schedules.append(LunchSchedule(date=target_date, menu=menu))

        for row in dinner_table.find_all("li"):
            value = row.text.strip()
            if "식사시간" in value:
                cafeteria_corner.operating_hours[MealType.DN].open_hours = value.split(
                    ":", maxsplit=1
                )[1].strip()
            elif "저녁메뉴" in value:
                menu = Menu(
                    name=value.split(":")[1].strip(),
                    price=None,
                    cafeteria_corner=cafeteria_corner,
                    vegetarian=False,
                    category=None,
                )
                schedules.append(DinnerSchedule(date=target_date, menu=menu))
            elif "예약전화" in value:
                cafeteria_corner.cafeteria_tel = value.split(":")[1].strip()

        return schedules
