import json

from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.state import StatesGroup, State

from ..db.db import get_session, MEDIA_CONFIG
from ..db.db_interaction.check import check_file_by_id
from ..db.db_interaction.delete import delete_file_folder_link
from ..db.db_interaction.update import set_user_folder, change_user_cur_folder_to_upper_one

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
        file_type_id, file_tg_id = await check_file_by_id(session = session, file_id = file_id)
    
    if not file_type_id:
        await callback.answer("File not found", show_alert=True)
        return
        
    keyboard = await delete_file_button(
        file_id   = file_id,
        folder_id = cur_folder_id
    )
    
    # Send media based on type
    full_file_type = SHORTCUT_TO_TYPE_BY_ID[file_type_id]
    send_method    = getattr(bot, f"send_{full_file_type}")

    await send_method(
            chat_id=callback.message.chat.id,
            **{full_file_type: file_tg_id},
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

        is_link = await delete_file_folder_link(
            session   = session, 
            file_id   = file_id, 
            folder_id = folder_id
        )
        
        if not is_link:
            await callback.answer("File not found", show_alert=True)
            return
        
    await callback.answer("File deleted successfuly.", show_alert=True)

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "d"'))
async def handle_go_downer_folder(callback: CallbackQuery):
    data      = json.loads(callback.data)
    folder_id = data.get("f")

    async with get_session() as session:
    
        await set_user_folder(
            session   = session, 
            chat_id   = callback.message.chat.id, 
            folder_id = folder_id
        )
        
        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=callback.message.chat.id)

    await callback.message.edit_text(
        f"Folder {cur_folder_path}", 
        reply_markup=keyboard
    )

    await callback.answer("Folder changed!")
        

@callback_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "u"'))
async def handle_go_to_upper_folder(callback: CallbackQuery):
    
    async with get_session() as session:
        
        par_folder_id = await change_user_cur_folder_to_upper_one(
            session = session, 
            chat_id = callback.message.chat.id,
        )
        
        # Check if we're at root (no par_folder_id)
        if par_folder_id is None:
            await callback.answer("Can't go up: Current folder is the root", show_alert=True)
            return
        
        par_folder_path, keyboard = await render_keyboard(session=session, chat_id=callback.message.chat.id)
        
    await callback.message.edit_text(
        f"Folder {par_folder_path}", 
        reply_markup=keyboard
    )

    await callback.answer("Folder changed!")
        