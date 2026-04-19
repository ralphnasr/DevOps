import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from shared.auth import AdminUser, CurrentUser
from shared.config import settings
from shared.models import Base, Category, Product


# ── Test database ──

def _derive_test_db_url(url: str) -> str:
    # Only swap the database name (path component), not user/host segments
    # that may also literally contain "shopcloud".
    base, _, _ = url.rpartition("/")
    return f"{base}/shopcloud_test"


TEST_DB_URL = _derive_test_db_url(settings.database_url)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    # NullPool prevents asyncpg connections from being reused across tests under
    # a session-scoped event loop, which otherwise raises "another operation is in
    # progress" when SQLAlchemy hands out a stale connection.
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
    # Hard-clean: services under test may commit, so rollback alone isn't enough.
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


# ── Mock Redis ──

@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock(return_value=True)
    r.delete = AsyncMock(return_value=True)
    r.ping = AsyncMock(return_value=True)
    r.aclose = AsyncMock()
    return r


# ── Mock SQS ──

@pytest.fixture
def mock_sqs():
    client = MagicMock()
    client.send_message = MagicMock(return_value={"MessageId": "test-msg-id"})
    return client


# ── Auth fixtures ──

@pytest.fixture
def current_user():
    return CurrentUser(cognito_sub="test-user-123", email="test@example.com")


@pytest.fixture
def admin_user():
    return AdminUser(cognito_sub="admin-user-123", email="admin@example.com")


# ── Test data ──

@pytest_asyncio.fixture
async def sample_category(db_session: AsyncSession):
    cat = Category(name="Electronics", description="Electronic devices")
    db_session.add(cat)
    await db_session.flush()
    return cat


@pytest_asyncio.fixture
async def sample_products(db_session: AsyncSession, sample_category):
    products = []
    for i in range(3):
        p = Product(
            name=f"Test Product {i+1}",
            description=f"Description for product {i+1}",
            price=10.00 * (i + 1),
            category_id=sample_category.id,
            stock_quantity=50,
            is_active=True,
            attributes={"test_key": f"value_{i+1}"},
        )
        db_session.add(p)
        products.append(p)
    await db_session.flush()
    return products


# ── HTTP Client fixtures ──

def _get_catalog_client(db_session, current_user):
    from entrypoints.catalog import app
    from shared.database import get_db
    from shared.dependencies import get_current_user

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _get_cart_client(db_session, mock_redis, current_user):
    from entrypoints.cart import app
    from shared.database import get_db
    from shared.dependencies import get_current_user
    from shared.redis_client import get_redis

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_current_user] = lambda: current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _get_checkout_client(db_session, mock_redis, current_user):
    from entrypoints.checkout import app
    from shared.database import get_db
    from shared.dependencies import get_current_user
    from shared.redis_client import get_redis

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_current_user] = lambda: current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _get_admin_client(db_session, admin_user):
    from entrypoints.admin import app
    from shared.database import get_db
    from shared.dependencies import get_current_admin

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_admin] = lambda: admin_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
