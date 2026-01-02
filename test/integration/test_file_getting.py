from app.db import *
from app.db.db_interaction.check import check_file_by_id
from app.db.db_interaction.get import get_files_details_in_folder_by_path_chat_id_and_type,  get_files_by_type_and_chat_id

import pytest

@pytest.mark.asyncio
async def test_getting_one_file(session, two_files_in_root_created, create_folder):
    first_file_id = 1
        
    file_type_id, file_tg_id = await check_file_by_id(
        session = session,
        file_id = first_file_id
    )

#--
    assert file_type_id is not None

@pytest.mark.asyncio
async def test_getting_file_in_folder_by_its_type(session, two_files_in_root_created):
    
    user_chat_id = two_files_in_root_created["user_id"]
    file_name = two_files_in_root_created["file_name"]
    tg_id     = two_files_in_root_created["tg_id"]
    path         = "/"
    type_id      = 1
    
    files_result = await get_files_details_in_folder_by_path_chat_id_and_type(
            session = session,
            path    = path,
            chat_id = user_chat_id,
            type_id = type_id
        )

    assert len(files_result) == 2
    first_tg_id, fisrt_file_name = files_result[0]
    first_tg_id, fisrt_file_name == tg_id, file_name

@pytest.mark.asyncio
async def test_getting_file_by_file_type(session, two_files_in_root_created):
    
    user_chat_id = two_files_in_root_created["user_id"]
    file_name = two_files_in_root_created["file_name"]
    tg_id     = two_files_in_root_created["tg_id"]
    type_id      = 1
    
    true_files = await get_files_by_type_and_chat_id(
        session = session,
        type_id = type_id,
        chat_id = user_chat_id
    )

    assert len(true_files) == 2
    first_file, second_file = true_files
    assert first_file.id == 1
    assert first_file.file_name == file_name
    assert first_file.tg_id == tg_id
