from collections import defaultdict
from datetime import date
from enum import Enum

from pydantic import BaseModel


class MealType(str, Enum):
    BR = "BR"  # breakfast
    LU = "LU"  # lunch
    DN = "DN"  # dinner


class Category(str, Enum):
    # 한식
    KOREAN_SOUP = "한식>찌개/국밥"
    KOREAN_BIBIMBAP = "한식>비빔밥/덮밥"
    KOREAN_GRILLED = "한식>구이/볶음"
    KOREAN_NOODLE = "한식>면류"
    KOREAN_JORIM = "한식>조림"

    # 양식
    WESTERN_PASTA = "양식>파스타/그라탕"
    WESTERN_STEAK = "양식>스테이크/패스트푸드"

    # 중식
    CHINESE_NOODLE = "중식>면류"
    CHINESE_RICE = "중식>밥류"
    CHINESE_FRIED = "중식>튀김/요리"

    # 일식
    JAPANESE_SUSHI = "일식>초밥/회"
    JAPANESE_RICE = "일식>덮밥"
    JAPANESE_NOODLE = "일식>면류"

    # 기타
    ETC_FUSION = "기타>퓨전"
    ETC_SNACK = "기타>간식/분식"
    ETC_VEGETARIAN = "기타>채식/건강식"
    ETC_UNKNOWN = "기타"

    @classmethod
    def get_main_category(cls, category: "Category") -> str:
        return category.value.split(">")[0]

    @classmethod
    def get_sub_category(cls, category: "Category") -> str:
        return category.value.split(">")[1]


class OperatingHours(BaseModel):
    open_hours: str | None = None
    rush_hours: str | None = None
    last_order: str | None = None
    break_hours: str | None = None
    additional_info: list[str] = []


class CafeteriaCorner(BaseModel):
    name: str
    cafeteria_name: str
    cafeteria_tel: str | None = None
    grouped: bool = False
    price: str | None = None
    operating_hours: dict[MealType, OperatingHours] = defaultdict(OperatingHours)

    def __hash__(self):
        return hash((self.name, self.cafeteria_name))

    def __eq__(self, other):
        if not isinstance(other, CafeteriaCorner):
            return False
        return self.name == other.name and self.cafeteria_name == other.cafeteria_name


class Menu(BaseModel):
    name: str
    canonical_name: str | None = None
    price: str | None = None
    cafeteria_corner: CafeteriaCorner
    vegetarian: bool = False
    category: Category | None = None


class BaseSchedule(BaseModel):
    date: date
    menu: Menu


class BreakfastSchedule(BaseSchedule):
    meal_type: MealType = MealType.BR


class LunchSchedule(BaseSchedule):
    meal_type: MealType = MealType.LU


class DinnerSchedule(BaseSchedule):
    meal_type: MealType = MealType.DN
