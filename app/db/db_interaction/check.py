from typing import Optional

from sqlmodel import select, and_
from ..models import User, Folder, File, FileFolder

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def check_user(session: AsyncSession, chat_id: int) -> tuple[Optional[int], Optional[int]]:
     
    # looking for a current user's folder id 
    cur_user_id_and_folder_result = await session.execute(
         select(User.id, User.cur_folder_id)
         .where(User.chat_id == chat_id)
    )
    cur_user_id, cur_folder_id = cur_user_id_and_folder_result.one()
     
    return cur_user_id, cur_folder_id

async def check_cur_folder_by_chat_id(session: AsyncSession, chat_id: int) -> tuple[Optional[Folder], Optional[int]]:
    # looking for a current user's folder 
    folder_result = await session.execute(
        select(Folder, User.id)
        .join(User, User.cur_folder_id == Folder.id)
        .options(selectinload(Folder.child_folders))
        .options(selectinload(Folder.parent_folder))
        .where(User.chat_id == chat_id)
    )
    folder, user_id = folder_result.one_or_none()
    
    return folder, user_id

async def check_cur_folder_by_path_and_chat_id(session: AsyncSession, path: str, chat_id: int) -> tuple[Optional[int], bool]:
    
    folder, user_id = await check_cur_folder_by_chat_id(session, chat_id)
    
    folder_id = None
    is_user   = True if user_id else False
    print(f"Folder founded path = {folder.full_path}")
    if folder.full_path == path:
        folder_id = folder.id
    
    return folder_id, is_user

async def check_folder_by_path_and_chat_id(session: AsyncSession, path: str, chat_id: int) -> Optional[int]:
    
    # looking for a current user's folder 
    folder_result = await session.execute(
        select(Folder, User.id)
        .join(User, User.cur_folder_id == Folder.parent_folder_id)
        .where(
            User.chat_id == chat_id,
            Folder.full_path == path,       
        )
    )
    folder_id = folder_result.scalars().one_or_none()
    
    return folder_id 
    
async def check_file_by_id(session: AsyncSession, file_id: int) -> tuple[Optional[int], Optional[int]]:

    file_result = await session.execute(
            select(File.file_type, File.tg_id)
            .where(File.id == file_id)
        )
    file_type_id, file_tg_id = file_result.one_or_none()
        
    return file_type_id, file_tg_id

async def check_user_file_and_file_folder_link(
          session:       AsyncSession,
          chat_id:       int,
          file_tg_id:    str,
          file_shortcut: str
          ) -> tuple[Optional[bool], Optional[int], Optional[int], Optional[int]]:

    result = await session.execute(
        select(
            User.id, 
            User.cur_folder_id, 
            File.id,
            FileFolder
        )
        .select_from(User)
        .where(User.chat_id == chat_id)
        .outerjoin(File, and_(
            File.tg_id == file_tg_id,
            File.media_type.has(short_version=file_shortcut)
        ))
        .outerjoin(FileFolder, and_(
            FileFolder.file_id   == File.id,
            FileFolder.folder_id == User.cur_folder_id
        ))
    )
    cur_user_id, cur_folder_id, file_id, link = result.one_or_none()

    return (link is not None), cur_folder_id, cur_user_id, file_id

