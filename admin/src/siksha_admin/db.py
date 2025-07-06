from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import siksha_admin.config as admin_config

# DB 연결
engine = create_async_engine(
    f"mysql+aiomysql://{admin_config.DB_CONFIG['user']}:{admin_config.DB_CONFIG['password']}@"
    f"{admin_config.DB_CONFIG['host']}:{admin_config.DB_CONFIG['port']}/{admin_config.DB_CONFIG['db']}",
    echo=True,
)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """비동기 DB 세션을 생성하는 의존성 함수"""
    async with async_session_maker() as session:
        yield session
