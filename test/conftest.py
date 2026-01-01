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

from app.db.db_interaction.create import try_create_user_file_and_file_folder_link, create_new_folder, create_new_file
from app.db.models import Folder, MediaType, File

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
            user_name:    str   = "test_user"
        ):
        
        await try_create_user_file_and_file_folder_link(
            session      = session,
            user_chat_id = user_chat_id,
            user_name    = user_name
        )
        
    return _create_user

@pytest.fixture
async def create_media_type(session):
    async def _create_media_type(
            mediatype_id:  int = 1,
            short_version: str = "gif",
            tg_version:    str = "animation",
        ):
        
        mt_data = {
            "id"            : mediatype_id,
            "short_version" : short_version,
            "tg_version"    : tg_version,
        }

        media_type = MediaType(**mt_data)
        session.add(media_type)

    return _create_media_type

@pytest.fixture
async def create_folder(session):
    async def _create_folder(
            user_id:         int = 1,
            par_folder_id:   int = 1,
            new_folder_name: str = "new_folder",
            new_folder_path: str = "/new_folder/"
        ) -> int:
        
        new_folder = Folder(
            user_id          = user_id,
            parent_folder_id = par_folder_id,
            folder_name      = new_folder_name,
            full_path        = new_folder_path
        )
    
        new_folder_id = await create_new_folder(
            session    = session,
            new_folder = new_folder,
        )
        
        return new_folder_id
    
    return _create_folder

@pytest.fixture
async def create_file(session):
    async def _create_file(        
            mock_backup_id:  int = 12345,
            mock_file_tg_id: str = "1234567890",
            mock_file_type:  int = 1, #gif
            file_name:       str = "test_file",
            user_id:         int = 1,
            cur_folder_id:   int = 1,
        ):

        new_file = File(
            tg_id     = mock_file_tg_id,
            file_type = mock_file_type,
            backup_id = mock_backup_id,
        )

        await create_new_file(    
            session   = session, 
            new_file  = new_file,
            user_id   = user_id,
            file_name = file_name, 
            folder_id = cur_folder_id
        )

    return _create_file

@pytest.fixture
async def create_file_link(session):
    async def _create_file_link(        
            file_name:       str = "test_file",
            file_id:         int = 1234567890,
            user_id:         int = 1,
            cur_folder_id:   int = 1,
        ):

        await create_new_file(    
            session   = session, 
            file_id   = file_id,
            user_id   = user_id,
            file_name = file_name, 
            folder_id = cur_folder_id
        )

    return _create_file_link


@pytest.fixture
async def user_created(create_user):
    user_name    = "test_user"
    user_chat_id = 1

    return await create_user(
        user_chat_id = user_chat_id, 
        user_name    = user_name
    )

@pytest.fixture
async def media_type_created(create_media_type):
    mediatype_id  = 1
    short_version = "gif"
    tg_version    = "animation"
    
    await create_media_type(
        mediatype_id  = mediatype_id,
        short_version = short_version,
        tg_version    = tg_version
    )

    return mediatype_id

@pytest.fixture
async def folder_created(create_folder):
    new_folder_name = "new_folder"
    new_folder_path = "/new_folder/"
    par_folder_id   = 1
    user_id         = 1

    new_folder_id = await create_folder(
        user_id         = user_id,
        par_folder_id   = par_folder_id,
        new_folder_name = new_folder_name,
        new_folder_path = new_folder_path
    )    
    
    return new_folder_id

@pytest.fixture
async def two_files_in_root_created(media_type_created, user_created, create_file):
    # Files creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = media_type_created
    file_name       = "test_file"
    cur_folder_id   = 1
    user_id         = 1

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = user_id,
            cur_folder_id   = cur_folder_id
        )
    
    mock_sec_folder_tg_id = mock_file_tg_id[::-1]
    sec_file_name         = file_name[::-1]
    mock_sec_backup_id    = mock_backup_id+1
    
    await create_file(        
            mock_backup_id  = mock_sec_backup_id,
            mock_file_tg_id = mock_sec_folder_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = sec_file_name,
            user_id         = user_id,
            cur_folder_id   = cur_folder_id
        )
    
    return {
        "mock_backup_id" : mock_backup_id,
        "mock_file_tg_id": mock_file_tg_id,
        "mock_file_type":  mock_file_type,
        "file_name":       file_name,
        "folder_id":      cur_folder_id,
        "tg_id":          mock_file_tg_id,
        "user_id":        user_id
    }

    
    
    
