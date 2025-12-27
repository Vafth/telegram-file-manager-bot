from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
import pytest

@pytest.mark.asyncio
async def test_file_moving(create_user, session):
    
# User creating
    user_name       = "test_user"
    user_chat_id    = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

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

# Folder renaming
    new_folder_name = "test2"
    
    await update_folder_name_and_path(
        session   = session,
        folder_id = new_folder_id,
        new_name  = new_folder_name,
        old_path  = new_folder_path,
        new_path  = "/"+new_folder_name+"/"
        )

#---

    folder_result = await session.execute(
        select(Folder)
        .options(selectinload(Folder.child_folders))
        .options(selectinload(Folder.file_folders))
    )
    folders = folder_result.scalars().all()
    
    root_folder, new_folder = folders

    assert user.cur_folder_id == new_folder.id
    assert new_folder.folder_name == new_folder_name