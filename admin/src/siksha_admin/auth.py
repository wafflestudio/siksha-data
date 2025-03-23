from datetime import datetime, timedelta

import config as admin_config
import jwt
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

ALGORITHM = "HS256"


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not (isinstance(username, str) and isinstance(password, str)):
            return False

        authenticated = (username in admin_config.ADMIN_AUTH.keys()) and (password == admin_config.ADMIN_AUTH[username])

        if not authenticated:
            return False

        request.session["username"] = username
        request.session["token"] = self.generate_jwt(username)
        return authenticated

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        token_exists = token is not None
        token_verified = self.verify_jwt(token)

        return token_exists and token_verified

    @staticmethod
    def generate_jwt(username: str) -> str:
        expires_at = datetime.utcnow() + timedelta(seconds=admin_config.ADMIN_EXPIRE)
        payload = {
            "sub": username,
            "exp": expires_at,
        }
        jwt_token = jwt.encode(payload, admin_config.ADMIN_SECRET, algorithm=ALGORITHM)
        return jwt_token

    @staticmethod
    def verify_jwt(token: str) -> bool:
        try:
            payload = jwt.decode(token, admin_config.ADMIN_SECRET, algorithms=[ALGORITHM])
            if payload["sub"] not in admin_config.ADMIN_AUTH.keys():
                return False
            if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                return False
            return True
        except BaseException:
            return False


authentication_backend = AdminAuth(secret_key=admin_config.ADMIN_SECRET)
