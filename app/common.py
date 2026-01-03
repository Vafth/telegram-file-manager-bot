from typing import Optional
from aiogram.types import InlineKeyboardMarkup, BotCommand
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

help_guide = """
<b>File Manager Commands:</b>

<b>/fe</b> — File Explorer
├ <b>Add Folder:</b> Create a subfolder in current location
├ <b>Save File:</b> Send any file to save it in current folder
└ <b>Get File:</b> Click file button -> file sent to chat

<b>/rn</b> — Rename current folder

<b>/mv</b> — Move all files from current folder to target folder

<b>/rm</b> — Delete current folder
     <i>Note: Remaining files move to parent folder</i>

<b>Inline Mode:</b>

<b>Search by folder:</b>
  • Type folder path to see subfolders
  • <i>Example:</i> <code>@your_bot /your/</code>
  
<b>Search by file type:</b>
  • Type extension to see all matching files
  • <i>Example:</i> <code>@your_bot .gif</code> -> shows all gif files
  
<b>Search in specific folder:</b>
  • Combine path + extension (max 50 results)
  • <i>Example:</i> <code>@your_bot /your/saved/gifs/.gif</code>

<b>File Types:</b>
  <b>Animation:</b> <code>.gif</code>
  <b>Video:</b>     <code>.mp4</code>
  <b>Photo:</b>     <code>.png</code>
  <b>Audio:</b>     <code>.mp3</code>
  <b>Sticker:</b>   <code>.sti</code>
  <b>Document:</b>  <code>.doc</code>

"""

commands = [
        BotCommand(command = "start", description = "Start Command"),
        BotCommand(command = "help",  description = "User Guide"),
        BotCommand(command = "fe",    description = "Open File Explorer"),
        BotCommand(command = "rm",    description = "Remove current folder"),
        BotCommand(command = "rn",    description = "Rename current folder"),
        BotCommand(command = "mv",    description = "Move all files to another folder"),
    ]