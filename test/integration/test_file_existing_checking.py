from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import * 
import pytest

@pytest.mark.asyncio
async def test_file_not_exist_existing_check(create_user, session):

    fake_file_tg_id = "1234567890"
    file_shortcut   = ".gif"
    user_name       = "test_user"
    user_chat_id    = 1
    
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
    
    is_exist, cur_folder_id, cur_user_id, file_id = await check_file_folder_link(
        session       = session,
        chat_id       = user_chat_id,
        file_tg_id    = fake_file_tg_id,
        file_shortcut = file_shortcut
    )

    assert is_exist == False
    assert cur_folder_id == user.cur_folder_id
    assert cur_user_id == user.id
    assert file_id == None
    