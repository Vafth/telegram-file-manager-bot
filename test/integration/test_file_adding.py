from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
import pytest

@pytest.mark.asyncio
async def test_one_file_adding(create_user, session):
    # create a media type
    mt_data = {
        "id"            : 1,
        "short_version" : "gif",
        "tg_version"    : "animation",
    }
    media_type = MediaType(**mt_data)
    session.add(media_type)

    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    user_name       = "test_user"
    user_chat_id    = 1
    mock_backup_id  = 12345

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert user is not None
    
    new_file = File(
        tg_id     = mock_file_tg_id,
        file_type = mock_file_type,
        backup_id = mock_backup_id,
    )
    
    await create_new_file(    
            session   = session, 
            new_file  = new_file,
            user_id   = user.id,
            file_name = file_name, 
            folder_id = user.cur_folder_id
        )

    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    file = file_result.scalars().one_or_none()

    assert file is not None
    assert file.file_folders is not None
    assert file.file_folders[0].file_name == file_name
    assert file.file_folders[0].file_id   == new_file.id
    assert file.file_users[0].user_id     == user.id
    assert file.file_users[0].first_user_file_name == file_name

@pytest.mark.asyncio
async def test_two_file_adding(create_user, session):
    # create a media type
    mt_data = {
        "id"            : 1,
        "short_version" : "gif",
        "tg_version"    : "animation",
    }
    media_type = MediaType(**mt_data)
    session.add(media_type)

    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    user_name       = "test_user"
    user_chat_id    = 1
    mock_backup_id  = 12345

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert user is not None
    
    new_file = File(
        tg_id     = mock_file_tg_id,
        file_type = mock_file_type,
        backup_id = mock_backup_id,
    )
    second_new_file = File(
        tg_id     = mock_file_tg_id[::-1],
        file_type = mock_file_type,
        backup_id = mock_backup_id+1,
    )
    
    await create_new_file(    
            session   = session, 
            new_file  = new_file,
            user_id   = user.id,
            file_name = file_name, 
            folder_id = user.cur_folder_id
        )

    await create_new_file(    
            session   = session, 
            new_file  = second_new_file,
            user_id   = user.id,
            file_name = file_name[::-1], 
            folder_id = user.cur_folder_id
        )

    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    files = file_result.scalars().all()

    assert files is not None
    assert [file.file_folders is not None for file in files] == [True, True]
    assert [file.file_folders[0].file_name for file in files] == [file_name, file_name[::-1]]
    