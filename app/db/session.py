from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# pymysql does not support async; use aiomysql for async driver.
# Replace "mysql+pymysql" with "mysql+aiomysql" for async support.
async_database_url = settings.database_url.replace(
    "mysql+pymysql", "mysql+aiomysql"
)

engine = create_async_engine(
    async_database_url,
    echo=settings.app_env == "development",
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session