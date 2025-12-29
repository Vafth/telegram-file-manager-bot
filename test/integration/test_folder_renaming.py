from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
from app.db.db_interaction.update import set_user_folder, update_folder_name_and_path
import pytest

@pytest.mark.asyncio
async def test_file_moving(create_user, create_folder, session):
    
    # User creating
    user_name      = "test_user"
    user_chat_id   = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    # Create a new folder
    root_folder_id = 1
    cur_folder_path = "/"
    new_folder_name = "test1"
    new_folder_path = f"{cur_folder_path}{new_folder_name}/"
    user_id        = 1

    new_folder_id = await create_folder(
        user_id         = user_id,
        par_folder_id   = root_folder_id,
        new_folder_name = new_folder_name,
        new_folder_path = new_folder_path
    )

    # Move user to the new folder
    await set_user_folder(
        session   = session,
        chat_id   = user_chat_id,
        folder_id = new_folder_id
    )

    # Folder renaming
    folder_new_name = "test2"
    folder_new_path = f"{cur_folder_path}{folder_new_name}/"

    await update_folder_name_and_path(
        session   = session,
        folder_id = new_folder_id,
        new_name  = folder_new_name,
        old_path  = new_folder_path,
        new_path  = folder_new_path
    )

    #---
    folder_result = await session.execute(
        select(Folder)
        .options(selectinload(Folder.child_folders))
        .options(selectinload(Folder.file_folders))
    )
    root_folder, new_folder = folder_result.scalars().all()
    
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()
    
    assert user.cur_folder_id     == new_folder.id
    assert new_folder.folder_name == folder_new_name
    assert user.folders           == [root_folder, new_folder]