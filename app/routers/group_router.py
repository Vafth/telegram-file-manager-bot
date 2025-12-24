from aiogram import F, Router
from aiogram.filters import and_f
from aiogram.types import Message

from ..filters.allowed_groups import isGroup, groupIsAllowed

group_router = Router()

@group_router.message(and_f(isGroup(), groupIsAllowed()))
async def animation_uploading_via_group(message: Message):
    print(1234567890)
    await message.answer("FUck YOU")
