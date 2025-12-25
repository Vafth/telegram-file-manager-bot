import os
from typing import Optional

from sqlmodel import select
from ..db import *
from sqlalchemy.ext.asyncio import AsyncSession


async def create_new_user_with_folder(session: AsyncSession, user_chat_id: int, user_name: str):
    
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

async def  check_if_file_folder_link_exist(
          session: AsyncSession,
          chat_id: int,
          file_tg_id: str,
          file_shortcut: str
          ) -> tuple[bool,int, int, int,]:

        # looking for a current user's folder id 
        cur_user_id_and_folder_result = await session.execute(
            select(
                User.id,
                User.cur_folder_id
            ).where(
                User.chat_id == chat_id
            )
        )
        
        cur_user_id, cur_folder_id = cur_user_id_and_folder_result.one()

        # looking for a file with a corresponded file type
        file_result = await session.execute(
            select(File)
            .join(MediaType, File.file_type == MediaType.id)
            .where(File.tg_id == file_tg_id)
            .where(MediaType.short_version == file_shortcut)
        )
        file = file_result.scalars().one_or_none()
        
        file_id                  = None
        is_exist_in_cur_folder   = False
        
        if file:
            file_id = file.id
            # looking for a FileFolder link
            result = await session.execute(
                select(FileFolder)
                .where(FileFolder.folder_id==cur_folder_id)
                .where(FileFolder.file_id==file.id)
            )
            file_folder_link = result.scalars().one_or_none()
            if file_folder_link: is_exist_in_cur_folder = True

        return is_exist_in_cur_folder, cur_folder_id, cur_user_id, file_id


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
    