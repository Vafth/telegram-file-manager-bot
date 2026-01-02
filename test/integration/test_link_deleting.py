from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
from app.db.db_interaction.check import check_user_file_and_file_folder_link, check_cur_folder_by_chat_id, check_folder_by_path_and_chat_id
from app.db.db_interaction.update import set_user_folder, move_file_folder_links_up
from app.db.db_interaction.delete import delete_file_folder_link

import pytest

@pytest.mark.asyncio
async def test_file_folder_deleting(two_files_in_root_created, session):
    first_file_id, second_file_id = 1, 2
    root_folder_id = two_files_in_root_created["folder_id"]
    
    is_link = await delete_file_folder_link(
            session   = session, 
            file_id   = first_file_id, 
            folder_id = root_folder_id
        )
        
    assert is_link == True

#---
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
        .options(selectinload(User.file_users))
    )
    user = user_result.scalars().one_or_none()

    file_folder_result = await session.execute(
        select(FileFolder)
        .options(selectinload(FileFolder.file))
    )
    file_folder_link = file_folder_result.scalars().one_or_none()

    assert len(user.folders) == 1
    assert file_folder_link.file_id == second_file_id


@pytest.mark.asyncio
async def test_file_folder_deleting_two_users(two_user_created, media_type_created, create_file, create_file_link, session):
    first_username = two_user_created["first_username"]
    second_username = two_user_created["second_username"]
    first_user_chat_id = two_user_created["first_userchat_id"]
    second_user_chat_id = two_user_created["second_userchat_id"]
    
    # Files creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = media_type_created
    file_name       = "test_file"
    cur_folder_id   = 1

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = first_user_chat_id,
            cur_folder_id   = first_user_chat_id
        )    
    

    is_exist, cur_folder_id, cur_user_id, file_id = await check_user_file_and_file_folder_link(
        session       = session,
        chat_id       = 2,
        file_tg_id    = mock_file_tg_id,
        file_shortcut = "gif"
    )

    assert is_exist == False
    assert cur_folder_id == 2
    assert cur_user_id == 2
    assert file_id == 1

    await create_file_link(        
            file_name = "test_file",
            file_id   = 1,
            user_id   = second_user_chat_id,
            cur_folder_id  = second_user_chat_id,

        )
    
    is_link = await delete_file_folder_link(
            session   = session, 
            file_id   = 1, 
            folder_id = 1
        )
        
    assert is_link == True

#---
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
        .options(selectinload(User.file_users))
    )
    users = user_result.scalars().all()

    file_folder_result = await session.execute(
        select(FileFolder)
        .options(selectinload(FileFolder.file))
    )
    file_folder_link = file_folder_result.scalars().one_or_none()

    file_user_result = await session.execute(
        select(FileUser)
        .options(selectinload(FileUser.file))
    )
    file_user_links = file_user_result.scalars().all()

    first_user, second_user = users

    assert len(first_user.folders) == 1
    assert file_user_links[0].file == file_user_links[1].file == file_folder_link.file