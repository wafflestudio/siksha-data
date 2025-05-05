import logging
from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import PyJWTError
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

import siksha_admin.config as admin_config

from .auth_utils import verify_password
from .models import AdminUser

ALGORITHM = admin_config.ALGORITHM
logger = logging.getLogger(__name__)


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not (isinstance(username, str) and isinstance(password, str)):
            logger.warning(
                f"Invalid login attempt with non-string credentials from {request.client.host}"
            )
            return False

        # 데이터베이스에서 사용자 조회
        user = await self._get_user_by_username(username)
        if not user:
            logger.warning(
                f"Login attempt for non-existent user '{username}' from {request.client.host}"
            )
            return False

        # 비밀번호 검증
        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt for user '{username}' from {request.client.host}")
            return False

        if not user.is_active:
            logger.warning(
                f"Login attempt for inactive user '{username}' from {request.client.host}"
            )
            return False

        # 로그인 성공 시 세션 설정
        request.session["username"] = username
        request.session["user_role"] = user.role
        request.session["token"] = self.generate_jwt(username)

        # 마지막 로그인 시간 업데이트 (비동기 처리)
        self._update_last_login(username)

        logger.info(f"Successful login for user '{username}' from {request.client.host}")
        return True

    async def _get_user_by_username(self, username: str) -> AdminUser | None:
        """사용자명으로 사용자를 조회합니다."""
        try:
            async with AsyncSession(self.admin.engine) as session:
                result = await session.execute(
                    select(AdminUser).filter(AdminUser.username == username)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database error when fetching user: {e!s}")
            return None

    async def _update_last_login(self, username: str) -> None:
        """마지막 로그인 시간을 업데이트합니다."""
        try:
            async with AsyncSession(self.admin.engine) as session:
                result = await session.execute(
                    select(AdminUser).filter(AdminUser.username == username)
                )
                user = result.scalar_one_or_none()
                if user:
                    user.last_login = datetime.now(UTC)
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to update last login time: {e!s}")

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        # 토큰 검증 및 사용자 존재 확인
        username = self.verify_jwt(token)
        if not username:
            return False

        # 사용자가 DB에 존재하고 활성 상태인지 확인
        user = await self._get_user_by_username(username)
        if not user or not user.is_active:
            return False

        return True

    @staticmethod
    def generate_jwt(username: str) -> str:
        expires_at = datetime.now(UTC) + timedelta(seconds=admin_config.ADMIN_EXPIRE)
        payload = {"sub": username, "exp": expires_at, "iat": datetime.now(UTC), "type": "access"}
        jwt_token = jwt.encode(payload, admin_config.ADMIN_SECRET, algorithm=ALGORITHM)
        return jwt_token

    @staticmethod
    def verify_jwt(token: str) -> str | None:
        try:
            payload = jwt.decode(token, admin_config.ADMIN_SECRET, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                return None
            if payload.get("type") != "access":
                return None
            if datetime.fromtimestamp(payload["exp"], UTC) < datetime.now(UTC):
                return None
            return username
        except PyJWTError as e:
            logger.warning(f"JWT verification failed: {e!s}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e!s}")
            return None


authentication_backend = AdminAuth(secret_key=admin_config.ADMIN_SECRET)
