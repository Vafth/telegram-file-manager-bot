from aiogram import F, Router, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from sqlmodel import select

from ..filters.allowed_users import userIsAllowed, isPrivate
from ..db.db import get_session
from ..db import *

external_router = Router()
external_router.message.filter(userIsAllowed(), isPrivate())

@external_router.message(Command("get_audio_links"))
async def getting_the_list_of_links_to_audio(message: Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    folder_path = args[1] if len(args) > 1 else "/"
    
    async with get_session() as session:
        try:
            folder_query = select(Folder).where(Folder.full_path == folder_path)
            folder_result = await session.execute(folder_query)
            folder = folder_result.scalars().one_or_none()
            
            if not folder:
                await message.answer(f"Folder '{folder_path}' not found")
                return
            
            files_query = (
                select(File)
                .join(FileFolder)
                .where(
                    FileFolder.folder_id == folder.id,
                    File.file_type == "mp3"
                )
            )
            
            files_result = await session.execute(files_query)
            files = files_result.scalars().all()
            
            if not files:
                await message.answer(f"Fodler '{folder_path}' has no audio")
                return

            audio_links = []
            for file in files:
                try:
                    tg_file = await bot.get_file(file.tg_id)
                    file_url = f"https://api.telegram.org/file/bot{bot.token}/{tg_file.file_path}"
                    
                    audio_links.append({
                        "file_name": file.file_name,
                        "file_id": file.tg_id,
                        "url": file_url
                    })
                except Exception as e:
                    print(f"Error while getting the file url {file.file_name}: {e}")
            
            
            response = {
                "folder": folder_path,
                "total_files": len(audio_links),
                "files": audio_links
            }

            import json
            json_str = json.dumps(response, ensure_ascii=False, indent=2)
            
            if len(json_str) < 4000:
                await message.answer(
                    f"Total: {len(audio_links)}\n\n"
                    f"```json\n{json_str}\n```",
                    parse_mode="Markdown"
                )
            else:
                from io import BytesIO
                json_file = BytesIO(json_str.encode('utf-8'))
                json_file.name = f"audio_links_{folder.id}.json"
                
                await message.answer_document(
                    BufferedInputFile(json_file.getvalue(), filename=json_file.name),
                    caption=f"Total: {len(audio_links)}"
                )
                
        except Exception as e:
            print(f"Error while getting the list of links: {e}")
            await message.answer(f"Error: {str(e)}")
