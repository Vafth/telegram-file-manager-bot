import json

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State

from sqlmodel import select

from ..db import *
from app.common import render_keyboard

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
        # Get user
        user_result = await session.execute(
            select(User)
            .where(User.chat_id == message.chat.id)
        )
        cur_user = user_result.scalars().one_or_none()

        if not cur_user:
            await message.answer("User not found", show_alert=True)
            return

        cur_user.cur_folder_id = new_folder.id
        await session.commit()

        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=message.chat.id)
    
    await message.reply(
        f"New Folder {cur_folder_path}",
        reply_markup=keyboard)

    await state.clear()
