import os
import asyncio
from dotenv import load_dotenv

load_dotenv(
    dotenv_path = "./test/.env.test", 
    override    = True
)
DB_URL = os.getenv("DB_URL")

from aiogram.types import Message
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import pytest

from app.db.db_interaction import create_new_user_with_folder

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        url=DB_URL,
        connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def session(test_engine):
    async_session_maker = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session_maker() as session:
        await session.begin()
        
        yield session
        
        await session.rollback()

        await session.close()

@pytest.fixture
async def create_user(session):
    async def _create_user(
            user_chat_id: int   = 1,
            user_name: str = "test_user"
        ):
        
        await create_new_user_with_folder(
            session      = session,
            user_chat_id = user_chat_id,
            user_name    = user_name
        )
        
    return _create_user
