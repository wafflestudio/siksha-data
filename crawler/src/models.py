from collections import defaultdict
from datetime import date
from enum import Enum

from pydantic import BaseModel


class MealType(str, Enum):
    BR = "BR"  # breakfast
    LU = "LU"  # lunch
    DN = "DN"  # dinner


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


class Menu(BaseModel):
    name: str
    price: str | None = None
    cafeteria_corner: CafeteriaCorner
    vegetarian: bool = False
    category: str | None = None


class BaseSchedule(BaseModel):
    date: date
    menu: Menu


class BreakfastSchedule(BaseSchedule):
    meal_type: MealType = MealType.BR


class LunchSchedule(BaseSchedule):
    meal_type: MealType = MealType.LU


class DinnerSchedule(BaseSchedule):
    meal_type: MealType = MealType.DN
