from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import * 
import pytest

@pytest.mark.asyncio
async def test_registration(create_user, session):
    user_chat_id = 1
    user_name    = "test_user"
    
    await create_user(
        user_chat_id = user_chat_id, 
        user_name    = user_name
    )

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert user is not None
    assert user.chat_id       == user_chat_id
    assert user.cur_folder_id == 1
    assert len(user.folders)  == 1

    folder = user.folders[0]

    assert folder.parent_folder_id is None
    assert folder.folder_name == user_name
    assert folder.full_path   == '/'
    assert folder.user        == user
    assert folder.parent_folder is None

@pytest.mark.asyncio
async def test_two_registration(create_user, session):
    first_user_chat_id = 1
    first_user_name    = "test_user"
    
    await create_user(
        user_chat_id = first_user_chat_id, 
        user_name    = first_user_name
    )

    second_user_chat_id = 2
    second_user_name    = "second_test_user"
    
    await create_user(
        user_chat_id = second_user_chat_id, 
        user_name    = second_user_name
    )


    users_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    users = users_result.scalars().all()

    assert users is not None
    user_one, user_two = users
    assert user_one.chat_id == first_user_chat_id
    
    second_root_folder = user_two.folders[0]

    assert second_root_folder.parent_folder_id is None
    assert second_root_folder.folder_name == second_user_name
    assert second_root_folder.full_path   == '/'
    