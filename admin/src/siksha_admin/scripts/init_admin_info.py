import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select

from siksha_admin.config import admin_config

from ..auth_utils import hash_password
from ..models import AdminUser, Base


async def create_initial_admin():
    """초기 관리자 계정을 생성합니다."""
    engine = create_async_engine(admin_config.DATABASE_URL)

    # 테이블 생성 (필요한 경우)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        # 이미 존재하는지 확인
        result = await session.execute(select(AdminUser).filter_by(username="admin"))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("관리자 계정이 이미 존재합니다.")
            return

        # 관리자 계정 생성
        admin_user = AdminUser(
            username="admin",
            password_hash=hash_password("admin"),  # 실제 배포 시 보안성 높은 비밀번호로 변경 필요
            role="superadmin",
        )

        session.add(admin_user)
        await session.commit()
        print("관리자 계정이 생성되었습니다.")


if __name__ == "__main__":
    asyncio.run(create_initial_admin())
