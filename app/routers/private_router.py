import os
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from ..filters.allowed_users import userIsAllowed, isPrivate
from ..db import *
from app.common import render_keyboard, help_guide

private_router = Router()
private_router.message.filter(userIsAllowed(), isPrivate())

@private_router.message(Command("help"))
async def command_clear(message: Message):
    await message.answer(f"User Guide:")
    await message.reply(text=help_guide, parse_mode='HTML')


@private_router.message(CommandStart())
async def start_cmd(message: Message):
    chat_id:   int = message.chat.id
    user_name: str = message.from_user.username
    
    async with get_session() as session:

        cur_user_check = await create_new_user_with_folder(
                session   = session, 
                chat_id   = chat_id, 
                user_name = user_name
        )

        if not cur_user_check:
            await message.answer(
                f"Hello, {user_name}!"
                f"\nYour root folder was created successfully."
                f"\nHave fun!"
            )
            await message.reply(text=help_guide, parse_mode='HTML')

        else:
            await message.answer(
                f"Hello, {user_name}!"
                f"\nWelcome back!"
            )
            await message.reply(text=help_guide, parse_mode='HTML')

@private_router.message(Command("fe"))
async def get_folder_tree_cmd(message: Message):
    
    async with get_session() as session:
        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=message.chat.id)    
        
    await message.reply(
        f"Folder {cur_folder_path}", 
        reply_markup = keyboard
    )