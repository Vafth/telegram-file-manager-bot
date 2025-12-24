import json

from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlmodel import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import *
from ..keyboards.inline_kb import build_folder, delete_file_button, confirm_folder_deleting_button

callback_router = Router()

class FolderDeleting(StatesGroup):
    cur_folder_id = State()
    par_folder_id = State()
    
SHORTCUT_TO_TYPE_BY_ID = {item[2]: item[1] for item in MEDIA_CONFIG}

async def render_keyboard_by_folder_id(session: AsyncSession, folder_id: int) -> tuple[int, InlineKeyboardMarkup]:

    # Get folder with its subfolders
    folder_result = await session.execute(
        select(Folder) 
        .options(selectinload(Folder.child_folders))
        .where(Folder.id == folder_id)
    )
    folder = folder_result.scalars().one_or_none()
    
    folder_path = folder.full_path
    folders_in_folder = folder.child_folders

    # Get all file links in current folder with file details
    file_links_result = await session.execute(
        select(FileFolder, File, MediaType.short_version)
        .join(File, FileFolder.file_id == File.id)
        .join(MediaType, File.file_type == MediaType.id)
        .where(FileFolder.folder_id == folder_id)
    )
    file_data = file_links_result.all()
    
    files_in_par_folder: list[TrueFile] = []
    
    for link, file, short_version in file_data:
        true_file = TrueFile(
            id            = file.id,
            file_name     = link.file_name,
            tg_id         = file.tg_id,
            backup_id     = file.backup_id,
            short_version = short_version
        )
        files_in_par_folder.append(true_file)

    keyboard = await build_folder(
        folders_in_folder = folders_in_folder, 
        files_in_folder   = files_in_par_folder, 
        cur_folder_id     = folder_id)
    
    return (folder_path, keyboard)


@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "g'))
async def handle_get_media(callback: CallbackQuery, bot: Bot):
    data      = json.loads(callback.data)
    file_id   = data.get("f")
    cur_folder_id = data.get("o")

    if not file_id:
        await callback.answer("Invalid file.", show_alert=True)
        return
    
    async with get_session() as session:
        file_result = await session.execute(
            select(File)
            .where(File.id == file_id)
        )
        file = file_result.scalars().one_or_none()
        if not file:
            await callback.answer("File not found", show_alert=True)
            return
            
        keyboard = await delete_file_button(
            file_id=file_id,
            folder_id=cur_folder_id
        )
        
        # Send media based on type
        full_file_type = SHORTCUT_TO_TYPE_BY_ID[file.file_type]
        send_method = getattr(bot, f"send_{full_file_type}")

        await send_method(
                chat_id=callback.message.chat.id,
                **{full_file_type: file.tg_id},
                reply_markup=keyboard
            )
        
        await callback.answer("Media sent!")

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "df'))
async def handle_delete_media(callback: CallbackQuery, bot: Bot):
    data = json.loads(callback.data)
    file_id = data.get("f")
    folder_id = data.get("o")
    if not file_id:
        await callback.answer("Invalid file.", show_alert=True)
        return
    
    async with get_session() as session:
        link_result = await session.execute(
            select(FileFolder)
            .where(
                FileFolder.file_id == file_id,
                FileFolder.folder_id == folder_id
            )
        )
        link = link_result.scalars().one_or_none()
        
        if not link:
            await callback.answer("File not found", show_alert=True)
            return
        
        await session.delete(link)
        await session.commit()
        
    await callback.answer("File deleted successfuly.", show_alert=True)

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "d"'))
async def handle_go_downer_folder(callback: CallbackQuery, bot: Bot):
    data = json.loads(callback.data)
    cur_folder_id = data.get("f")

    async with get_session() as session:
    
        # Get user
        user_result = await session.execute(
            select(User)
            .where(User.chat_id == callback.message.chat.id)
        )
        cur_user = user_result.scalars().one_or_none()

        if not cur_user:
            await callback.answer("User not found", show_alert=True)
            return

        cur_user.cur_folder_id = cur_folder_id
        await session.commit()
        
        cur_folder_path, keyboard = await render_keyboard_by_folder_id(session=session, folder_id=cur_folder_id)

    await callback.message.edit_text(f"Folder {cur_folder_path}", 
                    reply_markup=keyboard)

    await callback.answer("Folder changed!")
        

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "u"'))
async def handle_go_to_upper_folder(callback: CallbackQuery, bot: Bot):
    data = json.loads(callback.data)
    cur_folder_id = data.get("f")
    
    async with get_session() as session:
        par_folder_result = await session.execute(
            select(Folder.parent_folder_id)
            .where(Folder.id == cur_folder_id)
        )
        par_folder_id = par_folder_result.scalars().one_or_none()
        
        # Check if we're at root (no parent)
        if par_folder_id is None:
            await callback.answer("Can't go up: Current folder is the root", show_alert=True)
            return
    
        # Get user
        user_result = await session.execute(
            select(User)
            .where(User.chat_id == callback.message.chat.id)
        )
        cur_user = user_result.scalars().one_or_none()

        if not cur_user:
            await callback.answer("User not found", show_alert=True)
            return

        cur_user.cur_folder_id = par_folder_id
        await session.commit()
        
        par_folder_path, keyboard = await render_keyboard_by_folder_id(session=session, folder_id=par_folder_id)
        
    await callback.message.edit_text(f"Folder {par_folder_path}", 
                    reply_markup=keyboard)

    await callback.answer("Folder changed!")
        
@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "dl'))
async def handle_delete_folder_confirm(callback: CallbackQuery, bot: Bot, state: State):
    data = json.loads(callback.data)
    cur_folder_id = data.get("f")

    if not cur_folder_id:
        await callback.answer("Invalid folder.", show_alert=True)
        return
    
    async with get_session() as session:
        folder_result = await session.execute(
            select(Folder) 
            .options(selectinload(Folder.child_folders))
            .where(Folder.id == cur_folder_id)
        )
        folder = folder_result.scalars().one_or_none()

    if not folder:
        await callback.answer("Folder not found", show_alert=True)
        return
    
    if not folder.parent_folder_id:
        await callback.answer("Can't delete the root folder", show_alert=True)
        return
    
    if folder.child_folders:
        await callback.answer("Can't delete folder: child folders exist", show_alert=True)
        return

    folder_path = folder.full_path
    
    keyboard = await confirm_folder_deleting_button(folder_id=cur_folder_id)
    
    await callback.message.edit_text(
        f"Confirm deleting folder '{folder_path}'\n"
        f"All remainig files will be moved to the parent folder", 
        reply_markup=keyboard)

    await callback.answer("Confirm check!")
    await state.update_data(
        cur_folder_id = cur_folder_id,
        par_folder_id = folder.parent_folder_id
        )    
    await state.set_state(FolderDeleting.par_folder_id) 

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "cd'), FolderDeleting.par_folder_id)
async def handle_delete_folder(callback: CallbackQuery, bot: Bot, state: State):
    data = json.loads(callback.data)
    confirmation = data.get("c")
    
    state_data = await state.get_data()
    cur_folder_id = state_data["cur_folder_id"]
    par_folder_id = state_data["par_folder_id"]
    
    moved_count = 0

    async with get_session() as session:
        
        if confirmation:
            # Update FileFolder links
            update_links_result = await session.execute(
                update(FileFolder)
                .where(FileFolder.folder_id == cur_folder_id)
                .values(folder_id=par_folder_id)
                .returning(FileFolder.file_id)
            )
            moved_files = update_links_result.scalars().all()
            moved_count = len(moved_files)

            print(f"Moved {moved_count} files from {cur_folder_id} to {par_folder_id}")

            # Now delete child
            await session.execute(
                delete(Folder)
                .where(Folder.id == cur_folder_id)
            )
            
            print(f"Successfully deleted folder {cur_folder_id}")
            
            # Update User's current folder
            await session.execute(
                update(User)
                .where(User.chat_id == callback.message.chat.id)
                .values(cur_folder_id = par_folder_id)
            )
            
            await session.commit()
            
            cur_folder_id = par_folder_id 

    cur_folder_path, keyboard = await render_keyboard_by_folder_id(session=session, folder_id=cur_folder_id)

    if confirmation:
        await callback.answer(f"Folder deleted!", show_alert=True)
    
    await callback.message.edit_text(
        f"Folder {cur_folder_path}", 
        reply_markup=keyboard)
    
    await state.clear()
    return
