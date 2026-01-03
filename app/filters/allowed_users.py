from aiogram.filters import Filter
from aiogram.types import Message
from aiogram import  Bot

class userIsAllowed(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, message: Message, bot: Bot) -> bool:
        print(
            f"Request to the Bot from: {message.chat.id}"
            )
        return message.from_user.id in bot.my_admin_list    

class isPrivate(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.chat.type=="private":
            return True
        return False