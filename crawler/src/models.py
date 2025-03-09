from collections import defaultdict
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MealType(str, Enum):
    BR = "BR"  # breakfast
    LU = "LU"  # lunch
    DN = "DN"  # dinner


class OperatingHours(BaseModel):
    open_hours: Optional[str] = None
    rush_hours: Optional[str] = None
    last_order: Optional[str] = None
    break_hours: Optional[str] = None
    additional_info: list[str] = []


class CafeteriaCorner(BaseModel):
    name: str
    cafeteria_name: str
    cafeteria_tel: Optional[str] = None
    grouped: bool = False
    price: Optional[str] = None
    operating_hours: dict[MealType, OperatingHours] = defaultdict(OperatingHours)


class Menu(BaseModel):
    name: str
    price: Optional[str] = None
    cafeteria_corner: CafeteriaCorner
    vegetarian: bool = False
    category: Optional[str] = None


class BaseSchedule(BaseModel):
    date: date
    menu: Menu


class BreakfastSchedule(BaseSchedule):
    meal_type: MealType = MealType.BR


class LunchSchedule(BaseSchedule):
    meal_type: MealType = MealType.LU


class DinnerSchedule(BaseSchedule):
    meal_type: MealType = MealType.DN
