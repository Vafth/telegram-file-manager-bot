from typing import Optional

from sqlmodel import select
from ..models import User, Folder, File, FileFolder, FileUser

from sqlalchemy.ext.asyncio import AsyncSession

async def try_create_user_file_and_file_folder_link(session: AsyncSession, user_chat_id: int, user_name: str):
    
    result = await session.execute(
         select(User.chat_id)
         .where(User.chat_id == user_chat_id)
    )
    cur_user_check = result.scalars().one_or_none()
    
    if cur_user_check is None:
        new_user = User(chat_id = user_chat_id)
        session.add(new_user)
        await session.flush()

        new_folder = Folder(
            user_id          = new_user.id,
            parent_folder_id = None,
            folder_name      = user_name,
            full_path        = "/"
        )

        session.add(new_folder)
        await session.flush()

        new_user.cur_folder_id = new_folder.id

        await session.flush()
        print(
            f"NEW USER : {new_user}"
        )

    return cur_user_check

async def create_new_file(
          session:   AsyncSession, 
          user_id:   int,
          file_name: str, 
          folder_id: int,
          new_file:  Optional[File] = None,
          file_id:   Optional[int] = None,
        ):
        
    if new_file:
        session.add(new_file)
        await session.flush()
        file_id = new_file.id

    existing_FileUserLink = await session.execute(
        select(FileUser)
        .where(
            FileUser.file_id == file_id,
            FileUser.user_id == user_id
        )
    )

    if not existing_FileUserLink.scalars().one_or_none():
        session.add(
            FileUser(
                user_id              = user_id,
                file_id              = file_id,
                first_user_file_name = file_name
            )
        )
    
    new_file_folder = FileFolder(
        folder_id = folder_id,
        file_id   = file_id,
        file_name = file_name,
    )
    
    session.add(new_file_folder)
    
    await session.flush()

async def create_new_folder(session: AsyncSession, new_folder: Folder):

    session.add(new_folder)
    await session.flush()
    
    return new_folder.id
