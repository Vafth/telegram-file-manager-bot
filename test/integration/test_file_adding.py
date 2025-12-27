from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
import pytest

@pytest.mark.asyncio
async def test_one_file_adding(create_user, create_file, create_media_type, session):
    # create a media type
# Create a media type
    await create_media_type(
        mediatype_id  = 1,
        short_version = "gif",
        tg_version    = "animation"
    )

    # User creating
    user_name       = "test_user"
    user_chat_id    = 1
    root_folder_id  = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    # Files creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    cur_folder_id   = root_folder_id

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )

#---
    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    file = file_result.scalars().one_or_none()

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.file_users))
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert file is not None
    assert file.file_folders is not None
    assert file.file_folders[0].file_name == file_name
    assert file.file_folders[0].file_id   == file.id
    assert file.file_users[0].user_id     == user.id
    assert file.file_users[0].first_user_file_name == file_name

@pytest.mark.asyncio
async def test_two_file_adding(two_files_in_root_created, session):
    
    file_name =  two_files_in_root_created["file_name"]
    
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert user is not None

    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    files = file_result.scalars().all()

    assert files is not None
    assert [file.file_folders is not None for file in files] == [True, True]
    assert [file.file_folders[0].file_name for file in files] == [file_name, file_name[::-1]]
    