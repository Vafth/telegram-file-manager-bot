import os
import json
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeChat

from .routers import *

from .db.db import engine, create_db_and_tables

load_dotenv()
TOKEN           = os.getenv("BOT_TOKEN")
is_ADMIN_SETUP  = os.getenv("ADMIN_SETUP")
ADMINS          = json.loads(os.getenv("ADMIN_LIST"))
GROUPS          = json.loads(os.getenv("GROUP_LIST"))
ALLOWED_UPDATES = json.loads(os.getenv("ALLOWED_UPDATES"))

bot = Bot(token = TOKEN)
bot.my_admin_list = ADMINS
bot.my_group_list = GROUPS

async def start_bot(bot: Bot):
    if bot.my_admin_list and is_ADMIN_SETUP:
        await bot.send_message(bot.my_admin_list[0], "Start")
    
    commands = [
        BotCommand(command = "start", description = "Start Command"),
        BotCommand(command = "help",  description = "User Guide"),
        BotCommand(command = "fe",    description = "Open File Explorer"),
        BotCommand(command = "rm",    description = "Remove current folder"),
        BotCommand(command = "rn",    description = "Rename current folder"),
        BotCommand(command = "mv",    description = "Move all files to another folder"),
    ]

    for chat_id in bot.my_admin_list:
        await bot.delete_my_commands(scope = BotCommandScopeChat(chat_id = chat_id))
        await bot.set_my_commands(commands, scope = BotCommandScopeChat(chat_id = chat_id))
    
    await create_db_and_tables()

async def stop_bot(bot: Bot):
    if bot.my_admin_list and is_ADMIN_SETUP:
        await bot.send_message(bot.my_admin_list[0], "Stop")
    
    await asyncio.sleep(0.5)
    await engine.dispose()

dp = Dispatcher()
if is_ADMIN_SETUP:
    dp.include_router(admin_router)
else:
    dp.include_router(private_router)
    dp.include_router(group_router)
    dp.include_router(inline_router)
    dp.include_router(callback_router)
    dp.include_router(add_folder_router)
    dp.include_router(add_file_router)
    dp.include_router(remove_folder_router)
    dp.include_router(rename_folder_router)
    dp.include_router(move_router)

async def main():
    
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)
    
    finally:
        await bot.session.close()
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stop")