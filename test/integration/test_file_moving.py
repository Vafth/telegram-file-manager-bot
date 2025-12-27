from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
import pytest

@pytest.mark.asyncio
async def test_file_moving(create_user, session):
    # create a media type
    mt_data = {
        "id"            : 1,
        "short_version" : "gif",
        "tg_version"    : "animation",
    }
    media_type = MediaType(**mt_data)
    session.add(media_type)

# User creating
    user_name       = "test_user"
    user_chat_id    = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

# Files creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"

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

# New folder creating
    cur_folder_path = user.cur_folder_id #"/"
    new_folder_name = "test1"
    new_folder_path = f"{cur_folder_path}{new_folder_name}/"
    new_folder_id = 2

    folder_id, is_user = await check_folder_by_path_and_chat(
        session   = session,
        path      = new_folder_path,
        chat_id   = user_chat_id
    )

    assert folder_id is None
    assert is_user

    new_folder = Folder(
            user_id          = 1,
            parent_folder_id = 1,
            folder_name      = new_folder_name,
            full_path        = new_folder_path
    )
    
    new_folder_id = await create_new_folder(
        session    = session,
        new_folder = new_folder,
    )
    
    await set_user_folder(
        session   = session,
        chat_id   = user_chat_id,
        folder_id = new_folder_id
    )

# Moving files from the root folder to the new one part one
    confirmation = True
    target_folder_path = new_folder_path
    
    target_folder_id, _ = await check_folder_by_path_and_chat(
        session = session,
        chat_id = user_chat_id,
        path    = target_folder_path
    )

    assert target_folder_id is not None
    
# Change folder to root

    user.cur_folder_id = 1

# Moving files from the root folder to the new one part two
    moved_count = await move_file_folder_links(
        session          = session,
        folder_id        = cur_folder_path,
        target_folder_id = target_folder_id,
    )

#---
    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    files = file_result.scalars().all()

    folder_result = await session.execute(
        select(Folder)
        .options(selectinload(Folder.child_folders))
        .options(selectinload(Folder.file_folders))
    )
    folders = folder_result.scalars().all()
    
    root_folder, new_folder = folders
    first_file, second_file = files

    assert user.cur_folder_id == root_folder.id
    assert first_file.file_folders[0].folder_id == second_file.file_folders[0].folder_id == new_folder.id
    assert root_folder.file_folders == []
    assert moved_count == 2