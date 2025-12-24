from aiogram.filters import Filter
from aiogram.types import Message, InlineQuery
from aiogram import  Bot

class userIsAllowed(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, message: Message, bot: Bot) -> bool:
        return message.from_user.id in bot.my_admin_list
    
class inlineUserIsAllowed(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, inline_query: InlineQuery, bot: Bot) -> bool:
        return inline_query.from_user.id in bot.my_admin_list
    

class isPrivate(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.chat.type=="private":
            return True
        return False