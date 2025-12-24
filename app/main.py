import os
import json
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router
from aiogram.types import BotCommand, BotCommandScopeDefault

# Comment out later
from .routers import *

from .db.db import engine, create_db_and_tables

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMINS = json.loads(os.getenv("ADMIN_LIST"))
GROUPS = json.loads(os.getenv("GROUP_LIST"))
ALLOWED_UPDATES = json.loads(os.getenv("ALLOWED_UPDATES"))

bot = Bot(token=TOKEN)
bot.my_admin_list = ADMINS
bot.my_group_list = GROUPS

async def start_bot(bot: Bot):
    if bot.my_admin_list:
        await bot.send_message(bot.my_admin_list[0], "Bot has awakened.")
    commands = [
        BotCommand(command="start", description="Start Command"),
        BotCommand(command="fs", description="Open File System"),
    ]

    #await bot.delete_my_commands(scope=bot.my_admin_list[0])
    #await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    
    print("Bot started and Menu Commands updated.")
    await create_db_and_tables()

async def stop_bot(bot: Bot):
    if bot.my_admin_list:
        for admin in bot.my_admin_list:
            admin = int(admin)
            await bot.send_message(admin, "Bot has fallen asleep.")

    await engine.dispose() 

dp = Dispatcher()
dp.include_router(private_router)
dp.include_router(group_router)
dp.include_router(inline_router)
dp.include_router(callback_router)
dp.include_router(add_folder_router)
#dp.include_router(admin_router)

async def main():
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping")
    