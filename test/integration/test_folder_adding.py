from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
from app.db.db_interaction.check import check_cur_folder_by_chat_id, check_folder_by_path_and_chat_id
from app.db.db_interaction.update import set_user_folder

import pytest

@pytest.mark.asyncio
async def test_one_folder_adding(create_user, create_folder, session):
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

    folder_id, _ = await check_folder_by_path_and_chat_id(
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

    # Move user to the new folder
    await set_user_folder(
        session   = session,
        chat_id   = user_chat_id,
        folder_id = new_folder_id
    )

#---
    # Refresh the root_folder so it re-queries its children
    await session.refresh(root_folder)
    
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
    folders = folder_result.scalars().all()

    root_folder, new_folder = folders

    assert user is not None
    assert user.folders is not None
    assert user.folders[1].folder_name      == new_folder_name
    assert user.folders[1].full_path        == new_folder_path
    assert user.folders[1].parent_folder_id == 1
    assert user.cur_folder_id               == folders[1].id

    assert root_folder.id == new_folder.parent_folder_id
    assert new_folder.parent_folder == root_folder
    assert root_folder.child_folders[0] == new_folder
