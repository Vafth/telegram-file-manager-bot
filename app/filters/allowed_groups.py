from aiogram.filters import Filter
from aiogram.types import Message
from aiogram import  Bot

class groupIsAllowed(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.chat.type=="supergroup":
            return message.chat.id in bot.my_group_list
        return True
    
class isGroup(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, message: Message) -> bool:
        if message.chat.type=="supergroup":
            return True
        return False