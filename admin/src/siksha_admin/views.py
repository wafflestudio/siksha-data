from typing import Any

from sqladmin import ModelView
from sqlalchemy import func, select
from starlette.requests import Request

from .models import (
    AdminUser,
    Board,
    Comment,
    CommentLike,
    CommentReport,
    Image,
    Menu,
    MenuLike,
    Post,
    PostLike,
    PostReport,
    Restaurant,
    RestaurantRequest,
    User,
    Version,
)


# Base Views for Role-based Access
class SuperAdminView(ModelView):
    """관리자(admin) 역할만 접근 가능한 뷰"""

    can_create = True
    is_async = True

    async def is_accessible(self, request: Request) -> bool:
        return request.session.get("user_role") == "admin"


class OwnerView(ModelView):
    """식당 주인(owner) 역할만 접근 가능한 뷰"""

    can_create = True
    is_async = True

    async def is_accessible(self, request: Request) -> bool:
        return request.session.get("user_role") == "owner"


# SuperAdmin Views
class VersionAdmin(SuperAdminView, model=Version):
    name = "App Version"
    name_plural = "App Versions"
    icon = "fa-solid fa-mobile-screen"
    column_list = ["id", "client_type", "version", "minimum_version", "created_at"]
    column_labels = {
        "client_type": "Client",
        "version": "Current Version",
        "minimum_version": "Minimum Version",
    }


class UserAdmin(SuperAdminView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    column_list = ["id", "nickname", "type", "identity", "created_at"]
    column_searchable_list = ["nickname", "identity"]
    column_details_exclude_list = ["password_hash"]  # Assuming there is one
    form_excluded_columns = ["created_at", "updated_at"]


class RestaurantAdmin(SuperAdminView, model=Restaurant):
    name = "Restaurant"
    name_plural = "Restaurants"
    icon = "fa-solid fa-building-user"
    column_list = ["id", "code", "name_kr", "addr", "created_at"]
    column_searchable_list = ["code", "name_kr"]
    form_excluded_columns = ["created_at", "updated_at"]


class MenuAdmin(SuperAdminView, model=Menu):
    name = "Menu"
    name_plural = "Menus"
    icon = "fa-solid fa-book-open"
    column_list = ["id", "restaurant.name_kr", "name_kr", "date", "type", "price"]
    column_labels = {"restaurant.name_kr": "Restaurant"}
    column_searchable_list = ["name_kr"]
    form_excluded_columns = ["created_at", "updated_at"]
    # For faster loading in forms with many restaurants
    form_ajax_refs = {
        "restaurant": {
            "fields": ("name_kr", "code"),
            "order_by": "name_kr",
        },
    }


class AdminUserAdmin(SuperAdminView, model=AdminUser):
    name = "Admin User"
    name_plural = "Admin Users"
    icon = "fa-solid fa-user-shield"
    column_list = ["id", "username", "role", "is_active", "last_login", "owned_restaurants_count"]
    column_searchable_list = ["username"]
    column_filters = ["role", "is_active"]
    form_columns = ["username", "role", "is_active"]

    # 역할별 색상 구분
    column_formatters = {
        "role": lambda m, a: {
            "admin": "🔑 Admin",
            "owner": "🏪 Owner",
            "superadmin": "👑 Super Admin",
        }.get(m.role, m.role),
        "is_active": lambda m, a: "✅ Active" if m.is_active else "❌ Inactive",
    }

    async def get_query(self, request: Request):
        from sqlalchemy.orm import selectinload

        return (
            select(self.model)
            .options(selectinload(AdminUser.owned_restaurants))
            .order_by(self.model.role, self.model.username)
        )

    def owned_restaurants_count(self, model: AdminUser) -> str:
        """소유한 식당 수 표시"""
        if hasattr(model, "owned_restaurants") and model.owned_restaurants:
            count = len(model.owned_restaurants)
            restaurant_names = ", ".join([r.name_kr or r.code for r in model.owned_restaurants])
            return f"{count}개 ({restaurant_names})" if count > 0 else "없음"
        return "없음"


class RestaurantRequestAdmin(SuperAdminView, model=RestaurantRequest):
    name = "Restaurant Request"
    name_plural = "Restaurant Requests"
    icon = "fa-solid fa-file-signature"
    column_list = ["id", "restaurant_name", "owner_name", "phone", "status", "created_at"]
    column_searchable_list = ["restaurant_name", "owner_name"]
    form_excluded_columns = ["created_at", "updated_at", "processed_at"]

    # 상태별로 색상 구분
    column_formatters = {
        "status": lambda m, a: {
            "pending": "🟡 Pending",
            "approved": "🟢 Approved",
            "rejected": "🔴 Rejected",
        }.get(m.status, m.status)
    }

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        """RestaurantRequest 상태 변경 시 자동화 처리"""
        import logging

        from sqlalchemy import select
        from sqlalchemy.exc import IntegrityError

        # 승인 상태로 변경된 경우에만 처리
        if data.get("status") == "approved" and not is_created:
            restaurant_code = None
            try:
                async with self.session_maker() as session:
                    # 이미 등록된 Restaurant가 있는지 확인
                    existing_restaurant = await session.execute(
                        select(Restaurant).where(Restaurant.name_kr == model.restaurant_name)
                    )

                    if existing_restaurant.scalar_one_or_none() is None:
                        # Restaurant 코드 생성 (사업자번호 기반 또는 자동 생성)
                        restaurant_code = self._generate_restaurant_code(
                            model.business_number, model.restaurant_name
                        )

                        # AdminUser 생성 (식당 주인용 계정)
                        owner_admin = await self._create_owner_account(
                            session, restaurant_code, model
                        )

                        # 새로운 Restaurant 생성 (owner_id와 연결)
                        new_restaurant = Restaurant(
                            code=restaurant_code,
                            name_kr=model.restaurant_name,
                            addr=model.addr,
                            owner_id=owner_admin.id,
                            etc=f'{{"owner_name": "{model.owner_name}", "phone": "{model.phone}", "email": "{model.email or ""}"}}',  # noqa: E501
                        )

                        session.add(new_restaurant)
                        await session.commit()

                        logging.info(
                            f"새 식당 등록 완료: {model.restaurant_name} (코드: {restaurant_code}, owner: {owner_admin.username})"  # noqa: E501
                        )

                    else:
                        logging.warning(f"이미 등록된 식당입니다: {model.restaurant_name}")

            except IntegrityError as e:
                logging.error(f"식당 등록 중 오류 발생: {e}")
                raise ValueError(
                    "식당 등록 중 오류가 발생했습니다. 중복된 데이터가 있는지 확인해주세요."
                ) from e
            except Exception as e:
                logging.error(f"예상치 못한 오류: {e}")
                raise ValueError("식당 등록 중 예상치 못한 오류가 발생했습니다.") from e

        # 처리한 관리자 정보 기록
        if data.get("status") in ["approved", "rejected"] and not is_created:
            from sqlalchemy.sql import func

            data["processed_at"] = func.now()
            data["processed_by"] = request.session.get("username", "unknown")

            # 승인된 경우 생성된 식당 코드 기록
            if data.get("status") == "approved" and restaurant_code:
                data["restaurant_code"] = restaurant_code

    def _generate_restaurant_code(self, business_number: str, restaurant_name: str) -> str:
        """식당 코드 생성"""
        import hashlib
        import re

        if business_number:
            # 사업자번호 기반 코드 생성
            clean_number = re.sub(r"[^0-9]", "", business_number)
            return f"BN_{clean_number}"
        else:
            # 식당명 기반 해시 코드 생성
            hash_value = hashlib.md5(restaurant_name.encode("utf-8")).hexdigest()[:8]
            return f"REST_{hash_value.upper()}"

    async def _create_owner_account(
        self, session, restaurant_code: str, request_model
    ) -> AdminUser:
        """식당 주인용 관리자 계정 생성"""
        import secrets
        import string

        from sqlalchemy import select

        # 이미 계정이 있는지 확인
        existing_admin = await session.execute(
            select(AdminUser).where(AdminUser.username == restaurant_code)
        )

        existing_admin_user = existing_admin.scalar_one_or_none()
        if existing_admin_user is None:
            # 임시 비밀번호 생성
            temp_password = "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
            )

            # 비밀번호 해시화 (실제 구현에서는 bcrypt 등 사용)
            from siksha_admin.auth_utils import hash_password

            new_admin = AdminUser(
                username=restaurant_code,
                password_hash=hash_password(temp_password),
                role="owner",
                is_active=True,
            )

            session.add(new_admin)
            await session.flush()  # ID 생성을 위해 flush

            # 로그에 임시 비밀번호 기록 (실제로는 이메일 발송 등으로 처리)
            import logging

            logging.info(f"식당 주인 계정 생성: {restaurant_code}, 임시 비밀번호: {temp_password}")

            # TODO: 이메일로 계정 정보 발송
            # await self._send_account_info_email(
            #     request_model.email, restaurant_code, temp_password
            # )

            return new_admin
        else:
            return existing_admin_user

    async def _send_account_info_email(self, email: str, username: str, password: str) -> None:
        """계정 정보 이메일 발송 (구현 필요)"""
        # 이메일 발송 로직 구현
        pass


# Unchanged Admin views for brevity
class BoardAdmin(SuperAdminView, model=Board):
    icon = "fa-solid fa-table-list"
    column_list = [c.name for c in Board.__table__.c]


class PostAdmin(SuperAdminView, model=Post):
    icon = "fa-solid fa-file-lines"
    column_list = [c.name for c in Post.__table__.c]


class CommentAdmin(SuperAdminView, model=Comment):
    icon = "fa-solid fa-comment"
    column_list = [c.name for c in Comment.__table__.c]


class PostReportAdmin(SuperAdminView, model=PostReport):
    name_plural = "Post Reports"
    icon = "fa-solid fa-flag"
    column_list = [c.name for c in PostReport.__table__.c]


class CommentReportAdmin(SuperAdminView, model=CommentReport):
    name_plural = "Comment Reports"
    icon = "fa-solid fa-flag"
    column_list = [c.name for c in CommentReport.__table__.c]


# ... other simple admin views
class MenuLikeAdmin(SuperAdminView, model=MenuLike):
    column_list = [c.name for c in MenuLike.__table__.c]


class PostLikeAdmin(SuperAdminView, model=PostLike):
    column_list = [c.name for c in PostLike.__table__.c]


class CommentLikeAdmin(SuperAdminView, model=CommentLike):
    column_list = [c.name for c in CommentLike.__table__.c]


class ImageAdmin(SuperAdminView, model=Image):
    column_list = [c.name for c in Image.__table__.c]


# Restaurant Owner Views
class RestaurantOwnerAdmin(OwnerView, model=Restaurant):
    name = "My Restaurant"
    icon = "fa-solid fa-store"
    can_create = False
    can_delete = False
    # Owners can't change their unique code or other critical info
    form_excluded_columns = ["created_at", "updated_at", "code", "owner_id"]
    column_list = ["id", "code", "name_kr", "name_en", "addr", "lat", "lng"]
    column_searchable_list = ["name_kr", "name_en", "addr"]

    # Make some fields read-only for safety
    form_widget_args = {
        "id": {"readonly": True},
        "code": {"readonly": True},
    }

    async def get_query(self, request: Request):
        # Owners can only see their own restaurant
        user_id = request.session.get("user_id")
        return select(self.model).where(self.model.owner_id == user_id)

    async def get_count_query(self, request: Request):
        user_id = request.session.get("user_id")
        return (
            select(func.count(self.model.id))
            .select_from(self.model)
            .where(self.model.owner_id == user_id)
        )


class MenuOwnerAdmin(OwnerView, model=Menu):
    name = "My Menus"
    icon = "fa-solid fa-utensils"
    # Owners should not be able to assign a menu to another restaurant
    form_excluded_columns = ["created_at", "updated_at", "restaurant", "etc"]
    column_list = ["date", "type", "name_kr", "name_en", "price", "updated_at", "code"]
    column_searchable_list = ["name_kr", "name_en", "code"]
    column_sortable_list = ["date", "type", "name_kr", "price", "updated_at"]

    # 날짜별, 타입별 필터링 옵션 추가
    column_filters = ["date", "type"]

    # 폼에서 필드 설명 추가
    form_args = {
        "code": {"description": "메뉴 식별자 (공백 제거됨)"},
        "date": {"description": "메뉴 제공 날짜"},
        "type": {"description": "메뉴 타입 (BR: 아침, LU: 점심, DN: 저녁, AL: 종일)"},
        "name_kr": {"description": "한글 메뉴명"},
        "name_en": {"description": "영문 메뉴명"},
        "price": {"description": "가격 (원)"},
    }

    async def get_query(self, request: Request):
        # Owners can only see menus from their own restaurant
        user_id = request.session.get("user_id")
        return (
            select(self.model)
            .join(Restaurant)
            .where(Restaurant.owner_id == user_id)
            .order_by(self.model.date.desc(), self.model.type)
        )

    async def get_count_query(self, request: Request):
        user_id = request.session.get("user_id")
        return (
            select(func.count(self.model.id))
            .select_from(self.model)
            .join(Restaurant)
            .where(Restaurant.owner_id == user_id)
        )

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        # Automatically assign the owner's restaurant_id when creating/editing a menu
        user_id = request.session.get("user_id")
        async with self.session_maker() as session:
            result = await session.execute(
                select(Restaurant.id).where(Restaurant.owner_id == user_id)
            )
            restaurant_id = result.scalar_one_or_none()
            if restaurant_id:
                data["restaurant_id"] = restaurant_id
            else:
                raise ValueError("소유한 식당을 찾을 수 없습니다.")

        # 메뉴 코드에서 공백 제거
        if data.get("code"):
            data["code"] = data["code"].replace(" ", "")

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        """액션 권한 확인"""
        # 소유자는 자신의 메뉴만 수정/삭제 가능
        if name in ["edit", "delete", "details"]:
            user_id = request.session.get("user_id")
            model_id = request.path_params.get("pk")

            if model_id:
                async with self.session_maker() as session:
                    result = await session.execute(
                        select(self.model)
                        .join(Restaurant)
                        .where(self.model.id == model_id, Restaurant.owner_id == user_id)
                    )
                    return result.scalar_one_or_none() is not None

        return await super().is_action_allowed(request, name)
