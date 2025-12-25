from dotenv import load_dotenv
load_dotenv()

from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from sqlmodel import select, update, func

from ..filters.allowed_users import userIsAllowed, isPrivate
from ..db import *
from app.common import render_keyboard

rename_folder_router = Router()
rename_folder_router.message.filter(userIsAllowed(), isPrivate())

class FolderRenaming(StatesGroup):
    folder_id = State()
    old_path = State()

@rename_folder_router.message(Command("rn"))
async def handle_rename_folder_cmd(message: Message, state: State):
    
    async with get_session() as session:
        folder_result = await session.execute(
            select(Folder) 
            .join(User, Folder.id == User.cur_folder_id)
            .where(User.chat_id == message.chat.id)
        )
        folder = folder_result.scalars().one_or_none()

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

    # Calculate new path for the folder itself
    # Assuming path is like /home/documents
    path_parts = old_path.rstrip('/').split('/')
    path_parts[-1] = new_name
    new_path = "/".join(path_parts) + '/'

    print(
        f"Old path : {old_path}\n"
        f"New path : {new_path}"
    )

    async with get_session() as session:

        await session.execute(
            update(Folder)
            .where(Folder.id == folder_id)
            .values(folder_name=new_name)
        )   

        await session.execute(
            update(Folder)
            .where(Folder.full_path.startswith(old_path))
            .values(
                full_path=func.replace(Folder.full_path, old_path, new_path)
            )
        )

        await session.commit()
    
    cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=message.chat.id)

    await message.reply(
        f"Folder {cur_folder_path}", 
        reply_markup = keyboard
    )
    
    await state.clear()
    return

