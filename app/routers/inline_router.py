from typing import List

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResult, InlineQueryResultCachedGif, InlineQueryResultCachedAudio, InlineQueryResultCachedSticker, InlineQueryResultCachedPhoto, InlineQueryResultCachedVideo, InlineQueryResultCachedDocument, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton

from sqlmodel import select
from sqlalchemy.orm import selectinload

from ..filters.allowed_users import inlineUserIsAllowed
from ..db.db import get_session
from ..db import *
MAX_RESULTS = 50

MEDIA_TYPE_ID_MAP = {item[0]: item[2] for item in MEDIA_CONFIG}

def get_cached_result_class(short_type):
    info_map = {
        'gif': (InlineQueryResultCachedGif, 'gif_file_id'),
        'mp3': (InlineQueryResultCachedAudio, 'audio_file_id'),
        'png': (InlineQueryResultCachedPhoto, 'photo_file_id'),
        'mp4': (InlineQueryResultCachedVideo, 'video_file_id'),
        'sti': (InlineQueryResultCachedSticker, 'sticker_file_id'),
        'doc': (InlineQueryResultCachedDocument, 'document_file_id'),
    }
    return info_map.get(short_type)

inline_router = Router() 
inline_router.inline_query.filter(inlineUserIsAllowed())

@inline_router.inline_query()
async def handle_inline_get_media(inline_query: InlineQuery):
    
    query_text   = inline_query.query.strip() if inline_query.query else ""
    queries      = query_text.split(".")
    user_chat_id = inline_query.from_user.id

    if len(queries) == 2:
        search_type = 'folder' if queries[0] != "" else 'by_filetype'
    elif len(queries) == 0:
        search_type='help'
    else:
        search_type='folders_list'
    
    async with get_session() as session:

        user_result = await session.execute( 
            select(User)
            .where(User.chat_id == user_chat_id)
        )
        user = user_result.scalars().one_or_none()
        
        if not user:
            await inline_query.answer([])
            return
        
        results: List[InlineQueryResult] = []
        if search_type == "folder":

            file_ext = queries[1]
            type_id  = MEDIA_TYPE_ID_MAP.get(file_ext)
            
            if type_id is None:
                return await inline_query.answer([])

            folder_id_result = await session.execute(
                select(Folder.id)
                .where(Folder.full_path == queries[0],
                       Folder.user_id   == user.id
                )
            )
            cur_folder_id = folder_id_result.scalars().one_or_none()
            
            if not cur_folder_id:
                await inline_query.answer([]) 
                return
            
            files_result = await session.execute(
                select(File)
                .join(FileFolder)
                .where(
                    FileFolder.folder_id == cur_folder_id,
                    File.file_type == type_id
                )
                .limit(MAX_RESULTS)
            )
            
            files = files_result.scalars().all()
            
            if not files:
                await inline_query.answer([]) 
                return

            result_info = get_cached_result_class(file_ext)
            if not result_info: 
                return await inline_query.answer([])
            ResultClass, id_param = result_info
            
            for f in files:
                payload = {'id': f"file_{f.id}", id_param: f.tg_id}
                # Telegram REQUIRES title for these types
                if file_ext in ('mp3', 'mp4', 'doc'):
                    payload['title'] = f"File {f.id}.{file_ext}"
                
                results.append(ResultClass(**payload))

            
        elif search_type == "folders_list":

            folder_result = await session.execute(
                select(Folder)
                .options(
                    selectinload(Folder.child_folders)
                )
                .where(Folder.full_path == query_text,
                       Folder.user_id == user.id)
            )
            cur_folder = folder_result.scalars().one_or_none()
            
            if not cur_folder or not cur_folder.child_folders:
                empty_result = InlineQueryResultArticle(
                    id                    = "empty",
                    title                 = "Folder is empty",
                    description           = f"No sub-folders found in: {query_text}",
                    input_message_content = InputTextMessageContent(
                        message_text      = "This folder has no sub-folders to show."
                    )
                )
                return await inline_query.answer([empty_result])
            
            results = []
            for index, child_folder in enumerate(cur_folder.child_folders):
                result = InlineQueryResultArticle(
                    id                    = f"folder_{child_folder.id}_{index}",
                    title                 = child_folder.folder_name,
                    description           = child_folder.full_path,
                    input_message_content = InputTextMessageContent(
                        message_text      = f"Open: `{child_folder.full_path}`" 
                    ),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="Open", 
                            switch_inline_query_current_chat=child_folder.full_path 
                        )]
                    ])
                )
                results.append(result)

        elif search_type == "by_filetype":
            file_ext = queries[1]
            type_id = MEDIA_TYPE_ID_MAP.get(file_ext)
            
            if type_id is None:
                return await inline_query.answer([])

            files_result = await session.execute(
                select(File)
                .join(FileUser)
                .where(
                    FileUser.user_id == user.id,
                    File.file_type == type_id
                )
                .distinct()
                .limit(MAX_RESULTS)
            )
            files = files_result.scalars().all()
            
            result_info = get_cached_result_class(file_ext)
            if not result_info: 
                return await inline_query.answer([])
            ResultClass, id_param = result_info

            for f in files:
                payload = {'id': f"file_{f.id}", id_param: f.tg_id}
                # Telegram REQUIRES title for these types
                if file_ext in ('mp3', 'mp4', 'doc'):
                    payload['title'] = f"File {f.id}.{file_ext}"
                
                results.append(ResultClass(**payload))

        await inline_query.answer(
            results     = results,
            cache_time  = 0,
            is_personal = True
        )