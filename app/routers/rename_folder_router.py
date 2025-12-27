from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from ..filters.allowed_users import userIsAllowed, isPrivate
from ..db.db import get_session
from ..db.db_interaction import check_folder_by_chat_id, update_folder_name_and_path

from app.common import render_keyboard

rename_folder_router = Router()
rename_folder_router.message.filter(userIsAllowed(), isPrivate())

class FolderRenaming(StatesGroup):
    folder_id = State()
    old_path = State()

@rename_folder_router.message(Command("rn"))
async def handle_rename_folder_cmd(message: Message, state: State):
    
    async with get_session() as session:
        folder = await check_folder_by_chat_id(
            session = session,
            chat_id = message.chat.id
        )

    if not folder.parent_folder_id:
        await message.reply("Can't rename the root folder")
        return
    
    await message.reply(
        f"Old folder name: '{folder.folder_name}'\n"
        f"Provide the new name or retype the old one"
    )

    await state.update_data(
        folder_id = folder.id,
        old_path  = folder.full_path
    )    
    await state.set_state(FolderRenaming.folder_id) 
    
@rename_folder_router.message(FolderRenaming.folder_id)
async def handle_rename_folder(message: Message, state: State):
    
    state_data = await state.get_data()
    folder_id  = state_data["folder_id"]
    old_path   = state_data["old_path"]
    new_name   = message.text

    path_parts = old_path.rstrip('/').split('/')
    path_parts[-1] = new_name
    new_path = "/".join(path_parts) + '/'

    print(
        f"Old path : {old_path}\n"
        f"New path : {new_path}"
    )

    async with get_session() as session:

        await update_folder_name_and_path(
            session   = session,
            folder_id = folder_id,
            new_name  = new_name,
            old_path  = old_path,
            new_path  = new_path,
            )
    
        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=message.chat.id)

    await message.reply(
        f"Folder {cur_folder_path}", 
        reply_markup = keyboard
    )
    
    await state.clear()
    return

