import json

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State

from sqlmodel import select
from sqlalchemy.orm import selectinload


from ..keyboards.inline_kb import build_folder
from ..db import *


add_folder_router = Router()

class AddFolderStates(StatesGroup):
    fd_id = State()
    fd_path = State()
    fd_name = State()
    user_id = State()
    
@add_folder_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "add_fd"'))
async def handle_add_folder(callback: CallbackQuery, state: State):
    print("Creating a new folder")
    data = json.loads(callback.data)
    par_folder_id = data.get("fd_id")
    
    if not par_folder_id:
        await callback.answer("Invalid parent folder.", show_alert=True)
        return
    
    async with get_session() as session:
        folder_result = await session.execute(
            select(Folder, User.id)
            .join(User, User.cur_folder_id == Folder.id)
            .where(User.chat_id == callback.message.chat.id)
        )
        folder, user_id = folder_result.one_or_none()
        
        if not folder:
            await callback.answer("Folder not found", show_alert=True)
            return
        
    await callback.message.answer(f"Provide the new folder name")
    await state.update_data(
        fd_path = folder.full_path,
        fd_id   = folder.id,
        fd_name = folder.folder_name,
        user_id = user_id
    )
    await state.set_state(AddFolderStates.fd_name) 

@add_folder_router.message(AddFolderStates.fd_name)
async def providing_folder_name(message: Message, state: State):    
    
    await state.update_data(fd_name=message.text)
    data = await state.get_data()
    
    new_folder_path = f"{data['fd_path']}{data['fd_name']}/"
    
    new_folder = Folder(
            user_id           = data["user_id"],
            parent_folder_id = data["fd_id"],
            folder_name       = data["fd_name"],
            full_path         = new_folder_path
        )
    
    async with get_session() as session:
        session.add(new_folder)
        await session.commit()
        
        # Get current folder details
        folder_and_subfolders_result = await session.execute(
            select(Folder)
            .options(
                selectinload(Folder.child_folders)
            )
            .join(User, Folder.id == User.cur_folder_id)
            .where(User.chat_id == message.chat.id)
        )
        current_folder = folder_and_subfolders_result.scalars().one()
        
        cur_folder_path = current_folder.full_path
        cur_folder_id = current_folder.id
        folders_in_folder = current_folder.child_folders
        
        # Get all file links in current folder with file details
        file_links_result = await session.execute(
            select(FileFolder, File, MediaType.short_version)
            .join(File, FileFolder.file_id == File.id)
            .join(MediaType, File.file_type == MediaType.id)
            .where(FileFolder.folder_id == cur_folder_id)
        )
        file_data = file_links_result.all()
        
        files_in_folder: list[TrueFile] = []
        
        for link, file, short_version in file_data:
            true_file = TrueFile(
                id=file.id,
                file_name=link.file_name,
                tg_id=file.tg_id,
                backup_id=file.backup_id,
                short_version=short_version
            )
            files_in_folder.append(true_file)

    keyboard = await build_folder(
        folders_in_folder = folders_in_folder, 
        files_in_folder   = files_in_folder, 
        cur_folder_id     = cur_folder_id
    )
    
    await message.reply(
        f"New Folder {data['fd_path']}{data['fd_name']}/",
        reply_markup=keyboard)

    await state.clear()
