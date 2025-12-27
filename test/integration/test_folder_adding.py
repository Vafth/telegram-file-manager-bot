from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
import pytest

@pytest.mark.asyncio
async def test_one_folder_adding(create_user, session):

    user_name       = "test_user"
    user_chat_id    = 1
    cur_folder_path = "/"
    new_folder_name = "test1"
    new_folder_path = f"{cur_folder_path}{new_folder_name}/"
    
    await create_user(user_chat_id=user_chat_id, user_name=user_name)
    
    folder, user_id = await check_folder_by_chat_id(
        session = session,
        chat_id = user_chat_id
    )

    assert folder is not None
        
    folder_id, _ = await check_folder_by_path_and_chat(
        session   = session,
        path = new_folder_path,
        chat_id   = user_chat_id
    )

    assert folder_id is None

    new_folder = Folder(
            user_id          = 1,
            parent_folder_id = folder.id,
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
    folders = folder_result.scalars().all()

    assert user is not None
    assert user.folders is not None
    assert user.folders[1].folder_name      == new_folder_name
    assert user.folders[1].full_path        == new_folder_path
    assert user.folders[1].parent_folder_id == 1
    assert user.cur_folder_id               == folders[1].id

    assert folders[0].id == folders[1].parent_folder_id
    assert folders[0].child_folders[0] == folders[1]
    assert folders[1].parent_folder == folders[0]