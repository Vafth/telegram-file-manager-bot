from typing import Optional

from sqlmodel import select, exists, and_
from ..models import User, Folder, File, FileFolder, FileUser
from ..schema import TrueFile

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

async def get_overlap_files_number(
                session:          AsyncSession,
                folder_id:        int,
                target_folder_id: int,        
            ) -> int:
    print(f"Starting to grabbing the overlaping files")
    overlap_query = await session.execute(
        select(FileFolder.file_id)
        .where(FileFolder.folder_id == folder_id)
        .where(
            exists()
            .where(
                and_(
                    FileFolder.file_id == FileFolder.file_id, # matching same file
                    FileFolder.folder_id == target_folder_id
                )
            )
        )
    )
    overlaps = overlap_query.scalars().all()
    print(f"Overlaping files: {overlaps}")
    return len(overlaps)

async def get_folder_by_chat_id_and_path(session: AsyncSession, chat_id: int, path: str) -> Optional[Folder]:
    # get folder of the user woth the chat_id by path  
    folder_result = await session.execute(
        select(Folder)
        .join(User, User.chat_id == chat_id)
        .options(selectinload(Folder.child_folders))
        .options(selectinload(Folder.parent_folder))
        .where(Folder.full_path == path)
    )
    folder = folder_result.scalars().one_or_none()
    
    return folder

async def get_cur_folder_id_by_path_and_chat_id(session: AsyncSession, path: str, chat_id: int) -> tuple[Optional[int]]:
     
    folder_result = await session.execute(
        select(Folder.id)
        .join(User, User.chat_id == chat_id)
        .where(Folder.full_path == path)
    )
    folder_id = folder_result.scalars().one_or_none()
    
    return folder_id

async def get_files_details_in_folder_by_path_chat_id_and_type(
            session:     AsyncSession,
            path:        str,
            chat_id:     int,
            type_id:     int,
            max_results: int = 50
        ) -> list[Optional[tuple[str, str]]]:

    files_result = await session.execute(
        select(File.tg_id, FileFolder.file_name)
        .join(FileFolder, FileFolder.file_id == File.id)
        .join(Folder, Folder.id == FileFolder.folder_id)
        .join(User, User.id == Folder.user_id)
        .where(
            Folder.full_path == path,
            File.file_type == type_id,
            User.chat_id == chat_id
        )
        .limit(max_results)
    )
    files_details = files_result.all()
    return files_details

async def get_files_details_in_folder_by_type(
            session: AsyncSession,
            folder_id: int,
            type_id: int,
            max_results: int = 50
        ) -> list[Optional[list[int, int]]]:

    files_result = await session.execute(
        select(File.id, File.tg_id)
        .join(FileFolder)
        .where(
            FileFolder.folder_id == folder_id,
            File.file_type == type_id
        )
        .limit(max_results)
    )

    files_details = files_result.all()
    return files_details

async def get_files_by_type_and_chat_id(
            session: AsyncSession,
            type_id: int,
            chat_id: int,
            max_results: int = 50
        ) -> list[Optional[TrueFile]]:

    files_result = await session.execute(
        select(File, FileUser.first_user_file_name)
        .join(FileUser, FileUser.file_id == File.id)
        .join(User, User.id == FileUser.user_id)
        .where(
            User.chat_id   == chat_id,
            File.file_type == type_id
        )
        .distinct()
        .limit(max_results)
    )
    files = files_result.all()

    true_files: list[Optional[TrueFile]] = []
    
    for file, name in files:
        new_true_file = TrueFile(
            id        = file.id,
            file_name = name,
            tg_id     = file.tg_id
        )
        true_files.append(new_true_file)        
    
    return true_files