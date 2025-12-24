from aiogram import F, Router
from aiogram.types import Message

from aiogram.filters import Command, and_f
from ..filters.allowed_groups import isGroup

admin_router = Router()

@admin_router.message(Command("my_chat_id"))
async def get_my_chat_id(message: Message):
    await message.answer(
       f"Your chat id: {message.chat.id}"
    )

@admin_router.message(and_f(isGroup(), Command("get_group_and_thred_id")))
async def get_group_id_and_thread(message: Message):
    await message.answer(
       f"Your chat id   : {message.chat.id}\n"
       f"Your thread id : {message.message_thread_id}"
    )