from dotenv import load_dotenv
import json
load_dotenv()

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from ..filters.allowed_users import userIsAllowed, isPrivate
from ..db.db import get_session
from ..db.db_interaction import check_user, get_folder_id_by_path_and_chat_id, move_file_folder_links

from ..keyboards.inline_kb import confirm_file_moving_button
from app.common import render_keyboard

move_router = Router()
move_router.message.filter(userIsAllowed(), isPrivate())

class FoldersMoving(StatesGroup):
    cur_folder_id      = State()
    target_folder_path = State()
    target_folder_id   = State()
    confirm            = State()

@move_router.message(Command("mv"))
async def handle_move_cmd(message: Message, state: State):
    
    async with get_session() as session:

        _, cur_folder_id = await check_user(
            session = session,
            chat_id = message.chat.id
        )

    if not cur_folder_id:
        await message.answer(f"Folder not found")
        return

    await message.reply(
        f"Provide the full path to the folder where the files should be moved."
    )

    await state.update_data(
        cur_folder_id = cur_folder_id
    )    
    
    await state.set_state(FoldersMoving.target_folder_path) 

@move_router.message(FoldersMoving.target_folder_path)
async def handle_target_folder_path(message: Message, state: State):
    
    state_data      = await state.get_data()
    cur_folder_id   = state_data["cur_folder_id"]

    target_folder_path = message.text

    async with get_session() as session:

        target_folder_id = await get_folder_id_by_path_and_chat_id(
            session = session,
            chat_id = message.chat.id,
            path    = target_folder_path
        )
         
    if not target_folder_id:
        await message.answer(f"Moving canceled: Target folder {target_folder_path} not found")
        await state.clear()
        return
    
    keyboard = await confirm_file_moving_button(folder_id = cur_folder_id) 
    
    await message.reply(
        f"Confirm moving all files from the current folder\n"
        f"into folder `{target_folder_path}`", 
        reply_markup = keyboard
    )

    await state.update_data(
        target_folder_path = target_folder_path,
        target_folder_id   = target_folder_id,
    )    
    
    await state.set_state(FoldersMoving.confirm) 
    
@move_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "cm'), FoldersMoving.confirm)
async def handle_confirm_for_move_files(callback: CallbackQuery, state: State):
    data         = json.loads(callback.data)
    confirmation = data.get("c")
    
    state_data         = await state.get_data()
    cur_folder_id      = state_data["cur_folder_id"]
    target_folder_path = state_data["target_folder_path"]
    target_folder_id   = state_data["target_folder_id"]

    moved_count = 0

    async with get_session() as session:

        if confirmation:
    
            moved_count = await move_file_folder_links(
                session          = session,
                folder_id        = cur_folder_id,
                target_folder_id = target_folder_id,
            )

        cur_folder_path, keyboard = await render_keyboard(session = session, chat_id = callback.message.chat.id)

    if confirmation:
        await callback.answer(
            f"{moved_count} files were successfully moved"
            f"into folder {target_folder_path}!", 
            show_alert=True
        )
    
    await callback.message.edit_text(
        f"Folder {cur_folder_path}", 
        reply_markup=keyboard
    )
    
    await state.clear()
    return

