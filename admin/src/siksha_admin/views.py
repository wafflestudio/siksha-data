import logging

from sqladmin import ModelView
from sqlalchemy import Select, select
from starlette.requests import Request

from .models import AdminUser, Menu, Restaurant, Review

logger = logging.getLogger(__name__)


class BaseAdmin(ModelView):
    """기본 관리자 뷰 클래스로 인증 및 권한 검사 공통 기능 제공"""

    async def get_current_user(self, request: Request) -> AdminUser | None:
        """현재 로그인한 관리자 사용자 정보를 가져옵니다."""
        username = request.session.get("username")
        if not username:
            return None

        # 세션의 관리자 권한과 토큰이 있는지 확인
        user_role = request.session.get("user_role")
        token = request.session.get("token")
        if not (user_role and token):
            return None

        # AdminUser 모델에서 사용자 정보 조회
        async with self.admin.session_maker() as session:
            result = await session.execute(select(AdminUser).filter(AdminUser.username == username))
            user = result.scalar_one_or_none()

        return user

    async def is_accessible(self, request: Request) -> bool:
        """현재 사용자가 이 뷰에 접근 가능한지 확인합니다."""
        user = await self.get_current_user(request)
        if not user:
            return False

        # 기본적으로 활성 사용자만 접근 가능
        if not user.is_active:
            return False

        # 추가 권한 확인은 하위 클래스에서 구현
        return True


class MenuAdmin(BaseAdmin, model=Menu):
    column_list = [
        Menu.id,
        Menu.restaurant,
        Menu.name_kr,
        Menu.date,
        Menu.price,
        Menu.type,
        Menu.restaurant_id,
    ]

    column_formatters = {
        Menu.restaurant: lambda m, a: m.restaurant.name_kr,
    }
    column_searchable_list = [Menu.name_kr]
    column_sortable_list = [Menu.date]
    column_default_sort = (Menu.date, True)

    form_excluded_columns = [
        Menu.etc,
        Menu.created_at,
        Menu.updated_at,
        Menu.code,
        Menu.menu_likes,
        Menu.reviews,
    ]

    async def list_query(self, request: Request) -> Select:
        user = await self.get_current_user(request)

        if not user:
            # 비인증 상태라면 빈 쿼리 반환
            logger.warning("Unauthorized access attempt to MenuAdmin")
            return select(Menu).filter(Menu.id < 0)  # 항상 빈 결과 반환

        if user.role == "restaurant_owner":
            # 식당 소유자는 자신의 식당 메뉴만 볼 수 있음
            restaurant_id = request.session.get("restaurant_id")
            if restaurant_id and restaurant_id.isdigit():
                return select(Menu).filter(Menu.restaurant_id == int(restaurant_id))

        # 관리자는 모든 메뉴를 볼 수 있음
        return select(Menu)


class RestaurantAdmin(BaseAdmin, model=Restaurant):
    name = "Restaurant"
    name_plural = "Restaurants"

    column_list = [Restaurant.id, Restaurant.name_kr, Restaurant.addr, Restaurant.etc]
    form_excluded_columns = [Restaurant.menus]
    column_searchable_list = [Restaurant.name_kr]

    async def is_accessible(self, request: Request) -> bool:
        # 기본 접근성 검사
        is_accessible = await super().is_accessible(request)
        if not is_accessible:
            return False

        # 사용자 역할 기반 접근 제어
        user = await self.get_current_user(request)
        return user and (user.role in {"superadmin", "restaurant_owner"})

    async def list_query(self, request: Request) -> Select:
        user = await self.get_current_user(request)

        if not user:
            return select(Restaurant).filter(Restaurant.id < 0)  # 빈 결과

        if user.role == "restaurant_owner":
            # 식당 소유자는 자신의 식당만 볼 수 있음
            restaurant_id = request.session.get("restaurant_id")
            if restaurant_id and restaurant_id.isdigit():
                return select(Restaurant).filter(Restaurant.id == int(restaurant_id))

        # 관리자는 모든 식당을 볼 수 있음
        return select(Restaurant)


class ReviewAdmin(BaseAdmin, model=Review):
    can_edit = False
    can_export = True
    name = "Review"
    name_plural = "Reviews"
    column_default_sort = (Review.created_at, True)

    column_list = [Review.menu, Review.comment, Review.score]

    column_formatters = {
        Review.menu: lambda m, a: m.menu.name_kr,
    }

    async def list_query(self, request: Request) -> Select:
        user = await self.get_current_user(request)

        if not user:
            return select(Review).filter(Review.id < 0)  # 빈 결과

        if user.role == "restaurant_owner":
            # 식당 소유자는 자신의 식당에 대한 리뷰만 볼 수 있음
            restaurant_id = request.session.get("restaurant_id")
            if restaurant_id and restaurant_id.isdigit():
                return (
                    select(Review)
                    .join(Menu, onclause=(Menu.id == Review.menu_id))
                    .filter(Menu.restaurant_id == int(restaurant_id))
                )

        # 관리자는 모든 리뷰를 볼 수 있음
        return select(Review)


admin_views = [MenuAdmin, RestaurantAdmin, ReviewAdmin]
