from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
import pytest

@pytest.mark.asyncio
async def test_file_moving(session, two_files_in_root_created, create_folder):
    file_name      = two_files_in_root_created["file_name"]
    cur_folder_id  = two_files_in_root_created["folder_id"]
    user_chat_id   = 1
    root_folder_id = 1
    
    # New folder creating
    cur_folder_path = "/"
    new_folder_name = "test1"
    new_folder_path = f"{cur_folder_path}{new_folder_name}/"
    new_folder_id   = root_folder_id + 1

    new_folder_id = await create_folder(
        user_id         = 1,
        par_folder_id   = cur_folder_id,
        new_folder_name = new_folder_name,
        new_folder_path = new_folder_path
    )

    # Moving files from the root folder to the new one part two
    moved_count = await move_file_folder_links(
        session          = session,
        folder_id        = cur_folder_id,
        target_folder_id = new_folder_id,
    )

    # Move user to the new folder
    await set_user_folder(
        session   = session,
        chat_id   = user_chat_id,
        folder_id = new_folder_id
    )

    # Extra: Check file's existing
    first_file_type_id, first_file_tg_id   = await check_file(session = session, file_id = 1)
    second_file_type_id, second_file_tg_id = await check_file(session = session, file_id = 2)

#---
    # Get user
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.file_users))
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

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

    assert user.cur_folder_id == new_folder.id
    assert (first_file.tg_id, second_file.tg_id) == (first_file_tg_id, second_file_tg_id)
    assert (first_file.file_type, second_file.file_type) == (first_file_type_id, second_file_type_id)
    
    assert first_file.file_folders[0].folder_id == second_file.file_folders[0].folder_id == new_folder.id
    assert root_folder.file_folders == []
    assert new_folder.file_folders[0].file_name == file_name
    assert moved_count == 2