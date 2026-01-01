from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db import *
from app.db.db_interaction.check import check_user_file_and_file_folder_link
from app.db.db_interaction.update import set_user_folder
import pytest

@pytest.mark.asyncio
async def test_one_file_adding(create_user, create_file, create_media_type, session):
    # create a media type
# Create a media type
    await create_media_type(
        mediatype_id  = 1,
        short_version = "gif",
        tg_version    = "animation"
    )

    # User creating
    user_name       = "test_user"
    user_chat_id    = 1
    root_folder_id  = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    # Files creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    cur_folder_id   = root_folder_id

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )

#---
    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    file = file_result.scalars().one_or_none()

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.file_users))
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert file is not None
    assert file.file_folders is not None
    assert file.file_folders[0].file_name == file_name
    assert file.file_folders[0].file_id   == file.id
    assert file.file_users[0].user_id     == user.id
    assert file.file_users[0].first_user_file_name == file_name

@pytest.mark.asyncio
async def test_two_files_adding(two_files_in_root_created, session):
    
    file_name =  two_files_in_root_created["file_name"]
    
    user_result = await session.execute(
        select(User)
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert user is not None

    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    files = file_result.scalars().all()

    assert files is not None
    assert [file.file_folders is not None for file in files] == [True, True]
    assert [file.file_folders[0].file_name for file in files] == [file_name, file_name[::-1]]
    
@pytest.mark.asyncio
async def test_two_dif_files_adding_with_same_names_and_types(create_user, create_file, create_media_type, session):
    # Create a media type
    await create_media_type(
        mediatype_id  = 1,
        short_version = "gif",
        tg_version    = "animation"
    )

    # User creating
    user_name       = "test_user"
    user_chat_id    = 1
    root_folder_id  = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    # File creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    cur_folder_id   = root_folder_id
    mock_file_shortcut = "gif"

    is_exist, cur_folder_id, cur_user_id, file_id = await check_user_file_and_file_folder_link(
        session       = session,
        chat_id       = user_chat_id,
        file_tg_id    = mock_file_tg_id,
        file_shortcut = mock_file_shortcut
    )

    assert is_exist == False
    
    assert cur_user_id == True

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )

    # Seocnd file creating
    mock_backup_id  = 12346
    mock_file_tg_id = "1234567891"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    cur_folder_id   = root_folder_id

    is_exist, cur_folder_id, cur_user_id, file_id = await check_user_file_and_file_folder_link(
        session       = session,
        chat_id       = user_chat_id,
        file_tg_id    = mock_file_tg_id,
        file_shortcut = mock_file_shortcut
    )

    assert is_exist == False
    
    assert cur_user_id == True

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )

#---
    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    files = file_result.scalars().all()

    user_result = await session.execute(
        select(User)
        .options(selectinload(User.file_users))
        .options(selectinload(User.folders))
    )
    user = user_result.scalars().one_or_none()

    assert files is not None
    assert len(files) == 2
    first_file = files[0]
    assert first_file.file_folders is not None
    assert first_file.file_folders[0].file_name == file_name
    
@pytest.mark.asyncio
async def test_two_same_files_adding_with_same_names_and_types(create_user, create_file, create_media_type, session):
    # Create a media type
    await create_media_type(
        mediatype_id  = 1,
        short_version = "gif",
        tg_version    = "animation"
    )

    # User creating
    user_name       = "test_user"
    user_chat_id    = 1
    root_folder_id  = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    # File creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    cur_folder_id   = root_folder_id
    mock_file_shortcut = "gif"

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )


    is_exist, cur_folder_id, cur_user_id, file_id = await check_user_file_and_file_folder_link(
        session       = session,
        chat_id       = user_chat_id,
        file_tg_id    = mock_file_tg_id,
        file_shortcut = mock_file_shortcut
    )

    assert is_exist == True
    
    assert cur_user_id == True

#---
    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    files = file_result.scalars().all()

    assert files is not None
    assert len(files) == 1
    first_file = files[0]
    assert first_file.file_folders is not None
    assert first_file.file_folders[0].file_name == file_name
    
@pytest.mark.asyncio
async def test_two_dif_files_adding_with_same_names(create_user, create_file, create_media_type, session):
    # Create a media type
    await create_media_type(
        mediatype_id  = 1,
        short_version = "gif",
        tg_version    = "animation"
    )

    # Create a media type
    await create_media_type(
        mediatype_id  = 2,
        short_version = "mp3",
        tg_version    = "audio"
    )

    # User creating
    user_name       = "test_user"
    user_chat_id    = 1
    root_folder_id  = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    # File creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    cur_folder_id   = root_folder_id

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )

    mock_file_shortcut = "mp3"
    mock_backup_id  = 123456
    mock_file_tg_id = "1234567891"

    is_exist, cur_folder_id, cur_user_id, file_id = await check_user_file_and_file_folder_link(
        session       = session,
        chat_id       = user_chat_id,
        file_tg_id    = mock_file_tg_id,
        file_shortcut = mock_file_shortcut
    )

    assert is_exist == False
    
    assert cur_user_id == True

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )
#---

    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    files = file_result.scalars().all()
    
    assert files is not None
    assert len(files) == 2
    first_file, second_file = files
    assert first_file.file_folders is not None
    assert first_file.file_folders[0].file_name == file_name
    assert second_file.file_folders[0].file_name == file_name

@pytest.mark.asyncio
async def test_two_same_files_adding_with_same_names_in_dif_folders(create_user, create_file_link, create_file, create_media_type, create_folder, session):
    # Create a media type
    await create_media_type(
        mediatype_id  = 1,
        short_version = "gif",
        tg_version    = "animation"
    )

    # User creating
    user_name       = "test_user"
    user_chat_id    = 1
    root_folder_id  = 1

    await create_user(user_chat_id=user_chat_id, user_name=user_name)

    # File creating
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"
    mock_file_type  = 1 #gif
    file_name       = "test_file"
    cur_folder_id   = root_folder_id

    await create_file(        
            mock_backup_id  = mock_backup_id,
            mock_file_tg_id = mock_file_tg_id,
            mock_file_type  = mock_file_type,
            file_name       = file_name,
            user_id         = 1,
            cur_folder_id   = cur_folder_id
        )
    
    # New folder creating
    cur_folder_path = "/"
    new_folder_name = "test1"
    new_folder_path = f"{cur_folder_path}{new_folder_name}/"

    new_folder_id = await create_folder(
        user_id         = 1,
        par_folder_id   = cur_folder_id,
        new_folder_name = new_folder_name,
        new_folder_path = new_folder_path
    )

    # Move user to the new folder
    await set_user_folder(
        session   = session,
        chat_id   = user_chat_id,
        folder_id = new_folder_id
    )

    mock_file_shortcut = "gif"
    mock_backup_id  = 12345
    mock_file_tg_id = "1234567890"

    is_exist, cur_folder_id, cur_user_id, file_id = await check_user_file_and_file_folder_link(
        session       = session,
        chat_id       = user_chat_id,
        file_tg_id    = mock_file_tg_id,
        file_shortcut = mock_file_shortcut
    )

    assert is_exist == False
    
    assert cur_user_id == True

    assert file_id is not None

    await create_file_link(        
            file_name = "test_file",
            file_id   = file_id,
            user_id   = 1,
            cur_folder_id  = new_folder_id,

        )
#---

    file_result = await session.execute(
        select(File)
        .options(selectinload(File.file_folders))
        .options(selectinload(File.file_users))
    )
    file = file_result.scalars().one_or_none()
    
    file_folder_result = await session.execute(
        select(FileFolder)
        .options(selectinload(FileFolder.folder))
        .options(selectinload(FileFolder.file))
        )
    file_folder_links = file_folder_result.scalars().all()
    

    assert file is not None
    assert len(file_folder_links) == 2 
    first_link, second_link = file_folder_links
    assert first_link.file == second_link.file == file

