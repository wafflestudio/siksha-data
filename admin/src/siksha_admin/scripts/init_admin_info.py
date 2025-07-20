import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select

from ..auth_utils import hash_password
from ..config import DB_CONFIG
from ..models import AdminUser, Base, Restaurant


async def create_initial_data():
    """초기 관리자 및 테스트용 식당 데이터를 생성합니다."""

    engine = create_async_engine(
        f"mysql+aiomysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['db']}",
        echo=True,
    )

    # 테이블 생성 (필요한 경우)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        # 1. 관리자 계정 생성
        result = await session.execute(select(AdminUser).filter_by(username="admin"))
        if not result.scalar_one_or_none():
            admin_user = AdminUser(
                username="admin",
                password_hash=hash_password("admin"),
                role="admin",
            )
            session.add(admin_user)
            print("관리자 계정이 생성되었습니다.")
        else:
            print("관리자 계정이 이미 존재합니다.")

        # 2. 테스트용 식당 및 식당 주인 생성
        restaurant_code = "test_restaurant"
        result = await session.execute(select(Restaurant).filter_by(code=restaurant_code))
        if not result.scalar_one_or_none():
            restaurant = Restaurant(
                code=restaurant_code,
                name_kr="테스트 식당",
                name_en="Test Restaurant",
                addr="서울시 관악구",
            )
            session.add(restaurant)
            print(f"테스트 식당 '{restaurant_code}'가 생성되었습니다.")
        else:
            print(f"테스트 식당 '{restaurant_code}'가 이미 존재합니다.")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(create_initial_data())
