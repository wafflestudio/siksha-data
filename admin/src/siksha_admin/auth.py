import logging
from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import PyJWTError
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

import siksha_admin.config as admin_config

from .auth_utils import verify_password
from .db import async_session_maker
from .models import AdminUser, Restaurant

ALGORITHM = admin_config.ALGORITHM
logger = logging.getLogger(__name__)


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not (isinstance(username, str) and isinstance(password, str)):
            logger.warning(
                f"Invalid login attempt with non-string credentials from {request.client.host}"
            )
            return False

        # AdminUser 테이블에서 사용자 조회
        user = await self._get_user_by_username(username)
        if user:
            if not verify_password(password, user.password_hash):
                logger.warning(
                    f"Failed login attempt for user '{username}' from {request.client.host}"
                )
                return False
            if not user.is_active:
                logger.warning(
                    f"Login attempt for inactive user '{username}' from {request.client.host}"
                )
                return False

            request.session["username"] = username
            request.session["user_role"] = user.role
            request.session["user_id"] = user.id
            request.session["token"] = self.generate_jwt(username, user.role)

            await self._update_last_login(username)
            logger.info(
                f"Successful login for user '{username}' with role '{user.role}' from {request.client.host}"  # noqa: E501
            )
            return True

        logger.warning(
            f"Login attempt for non-existent user '{username}' from {request.client.host}"
        )
        return False

    async def _get_user_by_username(self, username: str) -> AdminUser | None:
        """사용자명으로 사용자를 조회합니다."""
        try:
            async with async_session_maker() as db:
                result = await db.execute(select(AdminUser).where(AdminUser.username == username))
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error when fetching user: {e!s}")
            return None

    async def _get_restaurant_user_by_code(self, code: str) -> Restaurant | None:
        """식당 코드로 식당을 조회합니다."""
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Restaurant)
                    .options(selectinload(Restaurant.owner))
                    .where(Restaurant.code == code)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error when fetching restaurant user: {e!s}")
            return None

    async def _update_last_login(self, username: str) -> None:
        """마지막 로그인 시간을 업데이트합니다."""
        try:
            async with async_session_maker() as db:
                result = await db.execute(select(AdminUser).filter(AdminUser.username == username))
                user = result.scalar_one_or_none()
                if user:
                    user.last_login = datetime.now(UTC)
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to update last login time: {e!s}")

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        verified = self.verify_jwt(token)
        if not verified:
            return False

        username, role = verified

        # AdminUser 테이블에서 사용자 확인
        user = await self._get_user_by_username(username)
        if user and user.is_active:
            return True

        return False

    @staticmethod
    def generate_jwt(username: str, role: str) -> str:
        expires_at = datetime.now(UTC) + timedelta(seconds=admin_config.ADMIN_EXPIRE)
        payload = {
            "sub": username,
            "role": role,
            "exp": expires_at,
            "iat": datetime.now(UTC),
            "type": "access",
        }
        jwt_token = jwt.encode(payload, admin_config.ADMIN_SECRET, algorithm=ALGORITHM)
        return jwt_token

    @staticmethod
    def verify_jwt(token: str) -> tuple[str, str] | None:
        try:
            payload = jwt.decode(token, admin_config.ADMIN_SECRET, algorithms=[ALGORITHM])
            username = payload.get("sub")
            role = payload.get("role")
            if not username or not role:
                return None
            if payload.get("type") != "access":
                return None
            if datetime.fromtimestamp(payload["exp"], UTC) < datetime.now(UTC):
                return None
            return username, role
        except PyJWTError as e:
            logger.warning(f"JWT verification failed: {e!s}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e!s}")
            return None


authentication_backend = AdminAuth(secret_key=admin_config.ADMIN_SECRET)
