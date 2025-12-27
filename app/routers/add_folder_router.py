import json

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State

from ..db.db import get_session
from ..db.models import Folder
from ..db.db_interaction import check_cur_folder_by_chat_id, check_folder_by_path_and_chat_id, create_new_folder, set_user_folder

from app.common import render_keyboard

add_folder_router = Router()

class AddFolderStates(StatesGroup):
    fd_id = State()
    fd_path = State()
    fd_name = State()
    user_id = State()
    
@add_folder_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "add_fd"'))
async def handle_add_folder(callback: CallbackQuery, state: State):

    data          = json.loads(callback.data)
    par_folder_id = data.get("fd_id")
    
    if not par_folder_id:
        await callback.answer("Invalid parent folder.", show_alert=True)
        return
    
    async with get_session() as session:
        
        folder, user_id = await check_cur_folder_by_chat_id(
            session = session,
            chat_id = callback.message.chat.id
        )

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
    
    async with get_session() as session:
        
        folder_id, is_user = await check_folder_by_path_and_chat_id(
            session   = session,
            full_path = new_folder_path,
            chat_id   = message.chat.id
        )

        if folder_id:
            await message.answer(
                f"Folder `{new_folder_path}` already exist.", 
                show_alert=True
            )
            return

        if not is_user:
            await message.answer(
                f"User not found.", 
                show_alert=True
            )
            return

        new_folder = Folder(
                user_id          = data["user_id"],
                parent_folder_id = data["fd_id"],
                folder_name      = data["fd_name"],
                full_path        = new_folder_path
        )
        
        new_folder_id = await create_new_folder(
            session    = session,
            new_folder = new_folder,
        )
        
        await set_user_folder(
            session   = session,
            chat_id   = message.chat.id,
            folder_id = new_folder_id
        )

        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=message.chat.id)
    
    await message.reply(
        f"New Folder {cur_folder_path}",
        reply_markup=keyboard
    )

    await state.clear()