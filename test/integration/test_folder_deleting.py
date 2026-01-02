from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
from app.db.db_interaction.check import check_cur_folder_by_chat_id, check_folder_by_path_and_chat_id
from app.db.db_interaction.update import set_user_folder, move_file_folder_links_up
from app.db.db_interaction.delete import delete_folder_by_id

import pytest

@pytest.mark.asyncio
async def test_one_folder_deleting(create_user, create_folder, session):
    # Create a new user 
    user_name    = "test_user"
    user_chat_id = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)
    # Check if user creating creates user and its folder
    root_folder, user_id = await check_cur_folder_by_chat_id(
        session = session,
        chat_id = user_chat_id
    )
    assert root_folder is not None
    
    # Check if the folder with target path are not in the db yet
    cur_folder_path = "/"
    new_folder_name = "test1"
    new_folder_path = f"{cur_folder_path}{new_folder_name}/"

    folder_id = await check_folder_by_path_and_chat_id(
        session   = session,
        path      = new_folder_path,
        chat_id   = user_chat_id
    )
    assert folder_id is None

    # Create a new folder
    new_folder_id = await create_folder(
        user_id         = user_id,
        par_folder_id   = root_folder.id,
        new_folder_name = new_folder_name,
        new_folder_path = new_folder_path
    )

    # Delete folder
    await delete_folder_by_id(session = session, folder_id = new_folder_id)

#---
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    folder_result = await session.execute(
        select(Folder)
        .options(selectinload(Folder.child_folders))
        .options(selectinload(Folder.parent_folder))
    )
    folders = folder_result.scalars().one_or_none()

    root_folder = folders
    assert root_folder.child_folders == []
    assert len(user.folders) == 1
    assert user.folders[0] == root_folder

@pytest.mark.asyncio
async def test_try_folder_failed_deleting(create_user, create_folder, session):
    # Create a new user 
    user_name    = "test_user"
    user_chat_id = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)
    # Check if user creating creates user and its folder
    root_folder, user_id = await check_cur_folder_by_chat_id(
        session = session,
        chat_id = user_chat_id
    )
    assert root_folder is not None

    # Check if the folder with target path are not in the db yet
    cur_folder_path = "/"
    new_folder_name = "test1"
    new_folder_path = f"{cur_folder_path}{new_folder_name}/"

    # Create a new folder
    new_folder_id = await create_folder(
        user_id         = user_id,
        par_folder_id   = root_folder.id,
        new_folder_name = new_folder_name,
        new_folder_path = new_folder_path
    )

#--    
    # Refresh the root_folder
    await session.refresh(root_folder)
    
    assert root_folder is not None
    
    assert root_folder.parent_folder_id is None
    
    assert root_folder.child_folders is not None

@pytest.mark.asyncio
async def test_deleting_folder_with_file(new_folder_with_file_created, session):
    
    # Update FileFolder links
    moved_count = await move_file_folder_links_up(
        session       = session,
        chat_id       = 1,
        par_folder_id = 1
    )
    assert moved_count >= 0
    
    # Update User's current folder
    await set_user_folder(
        session   = session, 
        chat_id   = 1, 
        folder_id = 1
    )
    
    # Delete folder
    await delete_folder_by_id(session = session, folder_id = 2)

    
#---
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    folder_result = await session.execute(
        select(Folder)
        .options(selectinload(Folder.child_folders))
        .options(selectinload(Folder.parent_folder))
    )
    folders = folder_result.scalars().one_or_none()

    file_folder_links = await session.execute(
        select(FileFolder)
        .options(selectinload(FileFolder.folder))
        .options(selectinload(FileFolder.file))
    )
    file_folder_links = file_folder_links.scalars().one_or_none()

    file_user_links = await session.execute(
        select(FileUser)
        .options(selectinload(FileUser.file))
    )
    file_user_links = file_user_links.scalars().one_or_none()

    root_folder = folders
    assert root_folder.child_folders == []
    assert len(user.folders) == 1
    assert user.folders[0] == root_folder

    assert file_folder_links.file == file_user_links.file
    assert file_folder_links.folder == root_folder

