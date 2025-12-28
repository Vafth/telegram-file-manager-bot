from typing import Optional

from sqlmodel import select, update, func, delete
from ..db import *

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

async def create_new_user_with_folder(session: AsyncSession, user_chat_id: int, user_name: str):
    
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


async def get_folder_id_by_path_and_chat_id(session: AsyncSession, path: str, chat_id: int) -> tuple[Optional[int]]:
     
    folder_result = await session.execute(
        select(Folder.id)
        .join(User, User.chat_id == chat_id)
        .where(Folder.full_path == path)
    )
    folder_id = folder_result.scalars().one_or_none()
    
    return folder_id

async def check_folder_by_path_and_chat_id(session: AsyncSession, path: str, chat_id: int) -> tuple[Optional[int], bool]:
    
    folder, user_id = await check_cur_folder_by_chat_id(session, chat_id)
    
    folder_id = None
    is_user   = True if user_id else False

    if folder.full_path == path:
        folder_id = folder.id
    
    return folder_id, is_user

async def check_file(session: AsyncSession, file_id: int) -> tuple[Optional[int], Optional[int]]:
    
    file_result = await session.execute(
            select(File.file_type, File.tg_id)
            .where(File.id == file_id)
        )
    file_type_id, file_tg_id = file_result.one_or_none()
        
    return file_type_id, file_tg_id

async def check_file_folder_link(
          session:       AsyncSession,
          chat_id:       int,
          file_tg_id:    str,
          file_shortcut: str
          ) -> tuple[bool, int, int, Optional[int]]:

        
    cur_user_id, cur_folder_id = await check_user(
            session = session, 
            chat_id = chat_id
    )
    
    # looking for a file with a corresponded file type
    file_result = await session.execute(
        select(File)
        .join(MediaType, File.file_type == MediaType.id)
        .where(File.tg_id == file_tg_id)
        .where(MediaType.short_version == file_shortcut)
    )
    file = file_result.scalars().one_or_none()
    
    file_id                = None
    is_exist_in_cur_folder = False
    
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

async def create_new_folder(session: AsyncSession, new_folder: Folder):

    session.add(new_folder)
    await session.flush()
    
    return new_folder.id


async def set_user_folder(session: AsyncSession, chat_id: int, folder_id: int):
    # Get user
    await session.execute(
        update(User)
        .where(User.chat_id == chat_id)
        .values(cur_folder_id = folder_id)
    )

async def move_file_folder_links_up(session: AsyncSession, chat_id: int, par_folder_id: int) -> int:
    
    # Update FileFolder links
    update_links_result = await session.execute(
        update(FileFolder)
        .where(
            FileFolder.folder_id == (
                select(User.cur_folder_id)
                .where(User.chat_id == chat_id)
                .scalar_subquery()
            )
        )
        .values(folder_id = par_folder_id)
        .returning(FileFolder.file_id)
    )

    moved_files = update_links_result.scalars().all()
    moved_count = len(moved_files)
    
    return moved_count

async def move_file_folder_links(
                session:          AsyncSession,
                folder_id:        int,
                target_folder_id: int,
            ) -> int:

    # Update FileFolder links
    update_links_result = await session.execute(
        update(FileFolder)
        .where(FileFolder.folder_id == folder_id)
        .values(folder_id=target_folder_id)
        .returning(FileFolder.file_id)
    )
    moved_files = update_links_result.scalars().all()
    
    moved_count = len(moved_files)
    print(f"Moved files count : {moved_count}")

    await session.flush() 
    
    return moved_count

async def update_folder_name_and_path(
            session: AsyncSession,
            folder_id: int,
            new_name: str,
            old_path: str,
            new_path: str,
            ):
    
    await session.execute(
        update(Folder)
        .where(Folder.id == folder_id)
        .values(folder_name=new_name)
    )   

    await session.execute(
        update(Folder)
        .where(Folder.full_path.startswith(old_path))
        .values(
            full_path=func.replace(Folder.full_path, old_path, new_path)
        )
    )

    await session.flush()

async def delete_link(
            session:   AsyncSession, 
            file_id:   int, 
            folder_id: int
        ) -> bool:

        link_result = await session.execute(
            select(FileFolder)
            .where(
                FileFolder.file_id == file_id,
                FileFolder.folder_id == folder_id
            )
        )
        link = link_result.scalars().one_or_none()
        
        if link:
            await session.delete(link)
            await session.flush()
        
        return True if link else False 

async def change_user_cur_folder_to_upper_one(session: AsyncSession, chat_id: int) -> tuple[Optional[int], Optional[User]]:
    
    par_folder_result = await session.execute(
        select(Folder.parent_folder_id, User)
        .join(User, User.cur_folder_id == Folder.id)
        .where(User.chat_id == chat_id)
    )
    par_folder_id, user = par_folder_result.one_or_none()

    if user and (par_folder_id is not None):
        user.cur_folder_id = par_folder_id
        await session.flush()

    return par_folder_id, user

async def delete_folder_by_id(session: AsyncSession, folder_id: int):
    
    await session.execute(
        delete(Folder)
        .where(Folder.id == folder_id)
    )

    await session.flush()
