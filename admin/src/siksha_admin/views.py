from data.db.models import Menu, Restaurant, Review
from sqladmin import ModelView
from sqlalchemy import Select, select
from starlette.requests import Request

"""
어드민 페이지 구성을 위한 템플릿 코드입니다

class UserAdmin(ModelView, model=User):
    column_list = [    # 보여줄 컬럼
    
    ]

    form_excluded_columns = [   # 제외할 컬럼

    ]

    column_searchable_list = [     # 검색할 컬럼

    ]

    column_sortable_list = User.__table__.columns.keys()
"""


class MenuAdmin(ModelView, model=Menu):
    column_list = [Menu.id, Menu.restaurant, Menu.name_kr, Menu.date, Menu.price, Menu.type, Menu.restaurant_id]

    column_formatters = {
        Menu.restaurant: lambda m, a: m.restaurant.name_kr,
    }
    column_searchable_list = [Menu.name_kr]
    column_sortable_list = [Menu.date]

    column_default_sort = (Menu.date, True)

    form_excluded_columns = [Menu.etc, Menu.created_at, Menu.updated_at, Menu.code, Menu.menu_likes, Menu.reviews]

    def list_query(self, request: Request) -> Select:
        username = request.session.get("username", "329")

        if username.isdigit():
            return select(Menu).filter(Menu.restaurant_id == int(username))
        else:
            return select(Menu).filter(Menu.restaurant_id == 329)  # Dummy, for test


class RestaurantAdmin(ModelView, model=Restaurant):
    column_list = [Restaurant.name_kr, Restaurant.addr, Restaurant.etc]

    column_searchable_list = [Restaurant.name_kr]

    column_formatters = {
        Restaurant.etc: lambda m, a: a,
    }

    form_excluded_columns = []

    def list_query(self, request: Request) -> Select:
        username = request.session.get("username", "329")

        if username.isdigit():
            return select(Restaurant).filter(Restaurant.id == int(username))
        else:
            return select(Restaurant).filter(Restaurant.id == 329)  # Dummy, for test


class ReviewAdmin(ModelView, model=Review):
    can_edit = False

    column_list = [Review.menu, Review.user, Review.comment, Review.score]

    column_formatters = {
        Review.user: lambda m, a: m.user.nickname,
        Review.menu: lambda m, a: m.menu.name_kr,
    }

    def list_query(self, request: Request) -> Select:
        return select(Review).join(Menu, onclause=(Menu.id == Review.menu_id)).filter(Menu.restaurant_id == 329)


admin_views = [MenuAdmin, RestaurantAdmin, ReviewAdmin]
