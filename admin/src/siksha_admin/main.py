from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.middleware.sessions import SessionMiddleware

import siksha_admin.config as admin_config

from .auth import AuthenticationBackend
from .views import admin_views

app = FastAPI()

# 세션 미들웨어 (로그인 세션 유지용)
app.add_middleware(SessionMiddleware, secret_key=admin_config.SECRET_KEY)

# DB 연결
engine = create_async_engine(admin_config.DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# SQLAdmin 초기화
admin = Admin(app, engine, authentication_backend=AuthenticationBackend())


# SQLAdmin 뷰 등록
for view in admin_views:
    admin.add_view(view)
