from dotenv import load_dotenv
import json
load_dotenv()

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

from ..filters.allowed_users import userIsAllowed, isPrivate
from ..db.db import get_session
from ..db.db_interaction import delete_folder_by_id, move_file_folder_links_up, check_cur_folder_by_chat_id, set_user_folder

from ..keyboards.inline_kb import confirm_folder_deleting_button
from app.common import render_keyboard

remove_folder_router = Router()
remove_folder_router.message.filter(userIsAllowed(), isPrivate())

class FolderDeleting(StatesGroup):
    cur_folder_id = State()
    par_folder_id = State()

@remove_folder_router.message(Command("rm"))
async def handle_remove_folder_cmd(message: Message, state: State):
    
    async with get_session() as session:
        
        folder, _ = await check_cur_folder_by_chat_id(
            session = session,
            chat_id = message.chat.id
        )

    if not folder:
        await message.answer(f"Folder `{folder.full_path}` not found")
        return
    
    if not folder.parent_folder_id:
        await message.reply("Can't delete the root folder")
        return
    
    if folder.child_folders:
        await message.reply(f"Can't delete folder `{folder.full_path}`: child folders exist")
        return

    folder_path = folder.full_path
    
    keyboard = await confirm_folder_deleting_button()
    
    await message.reply(
        f"Confirm removing folder '{folder_path}'\n"
        f"All remainig files will be moved to the parent folder", 
        reply_markup=keyboard
    )

    await state.update_data(
        cur_folder_id = folder.id,
        par_folder_id = folder.parent_folder_id
    )
    
    await state.set_state(FolderDeleting.par_folder_id) 
    
@remove_folder_router.callback_query(lambda c: c.data and c.data.startswith('{"a": "cd'), FolderDeleting.par_folder_id)
async def handle_delete_folder(callback: CallbackQuery, state: State):
    data = json.loads(callback.data)
    confirmation = data.get("c")
    
    state_data = await state.get_data()
    par_folder_id = state_data["par_folder_id"]
    cur_folder_id = state_data["cur_folder_id"]

    moved_count = 0

    async with get_session() as session:
        
        if confirmation:

            # Update FileFolder links
            moved_count = await move_file_folder_links_up(
                session       = session,
                chat_id       = callback.message.chat.id,
                par_folder_id = par_folder_id
            )


            # Update User's current folder
            await set_user_folder(
                session   = session, 
                chat_id   = callback.message.chat.id, 
                folder_id = par_folder_id
            )
            
            # Delete folder
            await delete_folder_by_id(session = session, folder_id = cur_folder_id)

        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=callback.message.chat.id)
    
    print(f"Successfully deleted folder {cur_folder_id}\n"
                  f"Moved files count : {moved_count}")
            
    if confirmation:
        await callback.answer(
            f"Folder deleted!"
            f"{moved_count} files were successfully moved!", 
            show_alert=True
        )

    await callback.message.edit_text(
        f"Folder {cur_folder_path}", 
        reply_markup=keyboard)
    
    await state.clear()
    return

