"""
Pytest configuration and fixtures for WOZ tests.
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    """Create test database session."""
    SessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False
    )
    
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_engine):
    """Create test client with test database."""
    from main import app
    from database import get_session
    
    # Override database session
    SessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False
    )
    
    async def override_get_session():
        async with SessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_session] = override_get_session
    
    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_wniosek_data():
    """Sample wniosek data for testing."""
    return {
        "title": "Test Wniosek",
        "person": "Jan Testowy",
        "company": "Test Company",
        "type_of_woz": "Standard",
        "payoff": 1500.00,
        "billing_month": "2026-01-01",
        "comment": "Test comment"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testtesttest",
        "full_name": "Test User"
    }
