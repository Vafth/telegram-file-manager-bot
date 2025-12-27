from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import * 
import pytest

@pytest.mark.asyncio
async def test_registration(create_user, session):
    user_chat_id = 1
    user_name    = "test_user"
    
    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert user is not None
    assert user.chat_id == user_chat_id
    assert user.cur_folder_id == 1
    assert len(user.folders) == 1

    folder = user.folders[0]

    assert folder.parent_folder_id is None
    assert folder.folder_name == user_name
    assert folder.full_path   == '/'
    assert folder.user == user
    assert folder.parent_folder is None
