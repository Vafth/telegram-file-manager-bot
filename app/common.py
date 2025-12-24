from typing import Optional
from aiogram.types import InlineKeyboardMarkup
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .db import *
from .keyboards.inline_kb import build_folder


async def render_keyboard(session: AsyncSession, folder_id: Optional[int] = None, 
                          chat_id: Optional[int] = None) -> tuple[int, InlineKeyboardMarkup]:

    query = (
        select(Folder).options(selectinload(Folder.child_folders))
    )
    if chat_id: query = (
        query
        .join(User, Folder.id == User.cur_folder_id)
        .where(User.chat_id == chat_id)
    )
    elif folder_id: query = query.where(Folder.id == folder_id)
    else:
        raise ValueError(f"Must provide either folder_id or chat_id")
    
    # Get current folder details
    folder_and_subfolders_result = await session.execute(query)
    folder = folder_and_subfolders_result.scalars().one()
    
    folder_path = folder.full_path
    folder_id = folder.id
    folders_in_folder = folder.child_folders
    
    # Get all file links in current folder with file details
    file_links_result = await session.execute(
        select(FileFolder, File, MediaType.short_version)
        .join(File, FileFolder.file_id == File.id)
        .join(MediaType, File.file_type == MediaType.id)
        .where(FileFolder.folder_id == folder_id)
    )
    file_data = file_links_result.all()
    
    files_in_folder: list[TrueFile] = []
    
    for link, file, short_version in file_data:
        true_file = TrueFile(
            id            = file.id,
            file_name     = link.file_name,
            tg_id         = file.tg_id,
            backup_id     = file.backup_id,
            short_version = short_version
        )
        files_in_folder.append(true_file)

    keyboard = await build_folder(
        folders_in_folder = folders_in_folder, 
        files_in_folder   = files_in_folder, 
        cur_folder_id     = folder_id
    )

    return (folder_path, keyboard)
