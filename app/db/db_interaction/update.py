from typing import Optional

from sqlmodel import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, Folder, FileFolder
from .get import get_overlap_files_number

async def move_file_folder_links_up(
        session: AsyncSession, 
        chat_id: int, 
        par_folder_id: int
    ) -> int:

    cur_folder_id_result = await session.execute(
        select(User.cur_folder_id)
        .where(User.chat_id == chat_id)
    )
    cur_folder_id = cur_folder_id_result.scalars().one_or_none()
    
    overlap_count = await get_overlap_files_number(
                session          = session,
                folder_id        = cur_folder_id,
                target_folder_id = par_folder_id,
    )
    
    if overlap_count == 0:
        # Update FileFolder links
        update_links_result = await session.execute(
            update(FileFolder)
            .where(FileFolder.folder_id == cur_folder_id)
            .values(folder_id = par_folder_id)
            .returning(FileFolder.file_id)
        )

        moved_files = update_links_result.scalars().all()
        moved_count = len(moved_files)
    else:
        moved_count = overlap_count * (-1)
    
    return moved_count

async def try_move_file_folder_links(
                session:          AsyncSession,
                folder_id:        int,
                target_folder_id: int,
            ) -> int:

    overlap_count = await get_overlap_files_number(
                session          = session,
                folder_id        = folder_id,
                target_folder_id = target_folder_id,
    )
    
    if overlap_count == 0:
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
    else:
        moved_count = overlap_count * (-1) 
    
    return moved_count

async def try_update_folder_name_and_path(
            session:   AsyncSession,
            folder_id: int,
            par_folder_id: int,
            new_name:  str,
            old_path:  str,
            new_path:  str,
        ) -> bool:
    
    folder_in_parent_folder = await session.execute(
        select(Folder)
        .where(
            Folder.parent_folder_id == par_folder_id,
            Folder.folder_name == new_name
        )
    )
    folder = folder_in_parent_folder.scalars().one_or_none()
    print(f"Folder finding result: {folder}, is it exist: {folder is not None}")
    is_folder = folder is not None
    
    if not is_folder:
        await session.execute(
            update(Folder)
            .where(Folder.id == folder_id)
            .values(folder_name = new_name)
        )   

        await session.execute(
            update(Folder)
            .where(Folder.full_path.startswith(old_path))
            .values(
                full_path=func.replace(Folder.full_path, old_path, new_path)
            )
        )

        await session.flush()
    
    return is_folder 

async def set_user_folder(session: AsyncSession, chat_id: int, folder_id: int):
    # Get user
    await session.execute(
        update(User)
        .where(User.chat_id == chat_id)
        .values(cur_folder_id = folder_id)
    )

async def change_user_cur_folder_to_upper_one(session: AsyncSession, chat_id: int) -> Optional[int]:
    
    parent_id_subquery = (
        select(Folder.parent_folder_id)
        .join(User, User.cur_folder_id == Folder.id)
        .where(User.chat_id == chat_id)
        .scalar_subquery()
    )

    go_upper = await session.execute(
        update(User)
        .where(User.chat_id == chat_id,
               parent_id_subquery.is_not(None)
               )
        .values(cur_folder_id = parent_id_subquery)
        .returning(User.cur_folder_id)
    )
    par_folder_id = go_upper.scalars().one_or_none()

    return par_folder_id