import json

from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.state import StatesGroup, State

from sqlmodel import select

from ..db import *
from ..keyboards.inline_kb import delete_file_button
from app.common import render_keyboard

callback_router = Router()

class FolderDeleting(StatesGroup):
    cur_folder_id = State()
    par_folder_id = State()
    
SHORTCUT_TO_TYPE_BY_ID = {item[2]: item[1] for item in MEDIA_CONFIG}

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "g'))
async def handle_get_media(callback: CallbackQuery, bot: Bot):
    data          = json.loads(callback.data)
    file_id       = data.get("f")
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
            file_id   = file_id,
            folder_id = cur_folder_id
        )
        
        # Send media based on type
        full_file_type = SHORTCUT_TO_TYPE_BY_ID[file.file_type]
        send_method    = getattr(bot, f"send_{full_file_type}")

        await send_method(
                chat_id=callback.message.chat.id,
                **{full_file_type: file.tg_id},
                reply_markup=keyboard
            )
        
        await callback.answer("Media sent!")

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "df'))
async def handle_delete_media(callback: CallbackQuery):
    data      = json.loads(callback.data)
    file_id   = data.get("f")
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
    data          = json.loads(callback.data)
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
        
        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=callback.message.chat.id)

    await callback.message.edit_text(
        f"Folder {cur_folder_path}", 
        reply_markup=keyboard
    )

    await callback.answer("Folder changed!")
        

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "u"'))
async def handle_go_to_upper_folder(callback: CallbackQuery, bot: Bot):
    data          = json.loads(callback.data)
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
        
        par_folder_path, keyboard = await render_keyboard(session=session, chat_id=callback.message.chat.id)
        
    await callback.message.edit_text(
        f"Folder {par_folder_path}", 
        reply_markup=keyboard
    )

    await callback.answer("Folder changed!")
        