import os

from aiogram import F, Router, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, or_f
from aiogram.fsm.state import StatesGroup, State

from sqlmodel import select

from ..filters.allowed_users import userIsAllowed, isPrivate
from ..db import *
from app.common import render_keyboard, help_guide

class FileAddingProccedData(StatesGroup):
    tg_file_id        = State()
    file_id           = State()
    file_name         = State()
    folder_id         = State()
    file_type         = State()
    file_type_id      = State()
    user_id           = State()
    current_folder_id = State()

# Generated Maps
MEDIA_TYPE_ID_MAP = {item[0]: item[2] for item in MEDIA_CONFIG}

async def get_file_info_from_message(message: Message):
    for shortcut, fullcut, _ in MEDIA_CONFIG:
        media = getattr(message, fullcut, None)
        if media:
            # Handle photo list exception
            file_obj = media[-1] if fullcut == 'photo' else media
            return file_obj.file_id, shortcut
    
    return None, None

async def get_file_info_by_shortcut(telegram_type):
    info_map = {
        'gif': ('animation', os.getenv('THREAD_GIF')),
        'mp3': ('audio',     os.getenv('THREAD_AUDIO')),
        'png': ('photo',     os.getenv('THREAD_IMAGE')),
        'mp4': ('video',     os.getenv('THREAD_VIDEO')),
        'sti': ('sticker',   os.getenv('THREAD_STICKER')),
        'doc': ('document',  os.getenv('THREAD_DOCUMENT')),
    }
    return info_map.get(telegram_type)

private_router = Router()
private_router.message.filter(userIsAllowed(), isPrivate())

@private_router.message(Command("help"))
async def command_clear(message: Message):
    await message.answer(f"User Guide:")
    await message.reply(text=help_guide, parse_mode='HTML')


@private_router.message(CommandStart())
async def start_cmd(message: Message):
    chat_id: int = message.chat.id
    user_name: str = message.from_user.username
    
    async with get_session() as session:
        result = await session.execute(select(User.chat_id).where(User.chat_id == chat_id))
        cur_user_check = result.scalars().one_or_none()
    
        if not cur_user_check:    
            new_user = User(chat_id=chat_id)
            session.add(new_user)
            await session.flush()

            new_folder = Folder(
                user_id          = new_user.id,
                parent_folder_id = None,
                folder_name      = user_name,
                full_path        = "/"
            )

            session.add(new_folder)
            await session.flush()

            new_user.cur_folder_id = new_folder.id

            await session.commit()
            print(
                f"NEW USER : {new_user}"
            )

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

@private_router.message(or_f((F.animation), (F.audio), (F.photo), (F.video), (F.sticker), (F.document)))
async def uploading_via_private(message: Message, state: State):

    chat_id = message.chat.id
    file_tg_id, file_shortcut = await get_file_info_from_message(message)
    
    # If a file type doesn't match in the map 
    if not file_tg_id:
        await message.reply("Unsupported file type!")
        return

    file_type_id = MEDIA_TYPE_ID_MAP[file_shortcut]

    await state.update_data(file_type=file_shortcut)
    print(f"FILE IS {file_shortcut}")
    
    
    async with get_session() as session:
        # looking for a current user's folder id 
        cur_user_id_and_folder_result = await session.execute(
            select(
                User.id,
                User.cur_folder_id
            ).where(
                User.chat_id == chat_id
            )
        )
        
        cur_user_id, cur_folder_id = cur_user_id_and_folder_result.one()

        # looking for a file with a corresponded file type
        file_result = await session.execute(
            select(File)
            .join(MediaType, File.file_type == MediaType.id)
            .where(File.tg_id == file_tg_id)
            .where(MediaType.short_version == file_shortcut)
        )
        file = file_result.scalars().one_or_none()
        
        file_id = None

        if file:
            file_id = file.id
            # looking for a FileFolder link
            result = await session.execute(
                select(FileFolder)
                .where(FileFolder.folder_id==cur_folder_id)
                .where(FileFolder.file_id==file.id)
            )
            file_folder_link = result.scalars().first()
            
            # if the link exists then drop an operation
            if file_folder_link:
                await message.reply(f"That File already is in the current folder!")
                await state.clear()
                return
            
    await message.reply(f"Provide the name of that File:")
    await state.update_data(
        tg_file_id   = file_tg_id,
        folder_id    = cur_folder_id,
        user_id      = cur_user_id,
        file_id      = file_id,
        file_type_id = file_type_id
    )
    
    await state.set_state(FileAddingProccedData.file_name) 

@private_router.message(F.text, FileAddingProccedData.file_name)
async def uploading_via_private_name_providing(message: Message, bot: Bot, state: State):    
    
    await state.update_data(file_name=message.text)
    data    = await state.get_data()
    file_id = data["file_id"]       
     
    async with get_session() as session:
        
        if file_id is None:

            full_file_type, group_threat = await get_file_info_by_shortcut(data["file_type"])
            
            method_name = f"send_{full_file_type}"
            send_method = getattr(bot, method_name)
            bot.send_checklist
            params = {
                "chat_id"          : bot.my_group_list[0],
                full_file_type     : data["tg_file_id"],
                "message_thread_id": group_threat,
            }

            sent_message = await send_method(**params)

            new_file = File( 
                tg_id     = data["tg_file_id"], 
                file_type = data["file_type_id"], 
                backup_id = sent_message.message_id
            )

            session.add(new_file)
            await session.flush()
            file_id = new_file.id

        existing_FileUserLink = await session.execute(
            select(FileUser)
            .where(
                FileUser.file_id == file_id,
                FileUser.user_id == data['user_id']
            )
        )

        if not existing_FileUserLink.scalars().one_or_none():
            session.add(
                FileUser(
                    user_id              = data['user_id'],
                    file_id              = file_id,
                    first_user_file_name = message.text
                )
            )
        
        new_file_folder = FileFolder(
            folder_id = data['folder_id'],
            file_id   = file_id,
            file_name = message.text,
        )
        
        session.add(new_file_folder)
        
        await session.commit()
    
    cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=message.chat.id)
    
    await message.reply(
        f"File has been added to the cur folder\nFolder {cur_folder_path}",
        reply_markup = keyboard
    )

    await state.clear()
        
@private_router.message(Command("fe"))
async def get_folder_tree_cmd(message: Message, bot: Bot):
    
    async with get_session() as session:
        cur_folder_path, keyboard = await render_keyboard(session=session, chat_id=message.chat.id)    
        
    await message.reply(
        f"Folder {cur_folder_path}", 
        reply_markup = keyboard
    )