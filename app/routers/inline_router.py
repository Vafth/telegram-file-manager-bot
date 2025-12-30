from typing import List

from aiogram import Router
from aiogram.types import (
    InlineQuery, InlineQueryResult, 
    InlineQueryResultCachedGif, InlineQueryResultCachedAudio, InlineQueryResultCachedSticker, 
    InlineQueryResultCachedPhoto, InlineQueryResultCachedVideo, InlineQueryResultCachedDocument, 
    InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
)

from ..filters.allowed_inline_queries import InlineSearchParser, inlineUserIsAllowed

from ..db import *
from ..db.db_interaction.get import get_files_details_in_folder_by_path_chat_id_and_type, get_folder_by_chat_id_and_path, get_files_by_type_and_chat_id

MAX_RESULTS = 50

MEDIA_TYPE_ID_MAP = {item[0]: item[2] for item in MEDIA_CONFIG}

def get_cached_result_class(short_type):
    info_map = {
        'gif': (InlineQueryResultCachedGif,      'gif_file_id'),
        'mp3': (InlineQueryResultCachedAudio,    'audio_file_id'),
        'png': (InlineQueryResultCachedPhoto,    'photo_file_id'),
        'mp4': (InlineQueryResultCachedVideo,    'video_file_id'),
        'sti': (InlineQueryResultCachedSticker,  'sticker_file_id'),
        'doc': (InlineQueryResultCachedDocument, 'document_file_id'),
    }
    return info_map.get(short_type)

inline_router = Router() 
inline_router.inline_query.filter(inlineUserIsAllowed())

@inline_router.inline_query(InlineSearchParser(target_type = "help"))
async def handle_help(inline_query: InlineQuery):
    # This is the text that appears in the chat if they click the article itself
    results = []

    # 1. Folder Search Article
    results.append(InlineQueryResultArticle(
        id="help_folders",
        title="Search by Folder",
        description="Type /path/ to see subfolders",
        input_message_content=InputTextMessageContent(message_text="How to search folders: type <code>/</code>"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Try it", switch_inline_query_current_chat="/")
        ]])
    ))

    # 2. Filetype Search Article
    results.append(InlineQueryResultArticle(
        id="help_files",
        title="Search by Filetype",
        description="Type .ext to find files (e.g. .pdf)",
        input_message_content=InputTextMessageContent(message_text="How to search by type: type <code>.gif</code>"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Try it", switch_inline_query_current_chat=".gif")
        ]])
    ))

    # 3. Specific Search Article
    results.append(InlineQueryResultArticle(
        id="help_specific",
        title="Search in Folder",
        description="Combine path and extension",
        input_message_content=InputTextMessageContent(message_text="Advanced search: <code>/path/.ext</code>"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Try it", switch_inline_query_current_chat="/my/gifs/.gif")
        ]])
    ))

    return await inline_query.answer(
        results=results,
        cache_time=0,
        is_personal=True
    )

@inline_router.inline_query(InlineSearchParser(target_type = "in_folder"))
async def handle_infolder_search(inline_query: InlineQuery, parts: list[str]):
    results: List[InlineQueryResult] = []

    user_chat_id = inline_query.from_user.id
    file_ext     = parts[1]
    path         = parts[0]
    
    type_id      = MEDIA_TYPE_ID_MAP.get(file_ext)
    
    if type_id is None:
        return await inline_query.answer([])

    result_info = get_cached_result_class(file_ext)
    
    if not result_info: 
        return await inline_query.answer([])
    
    ResultClass, id_param = result_info

    async with get_session() as session:
            
        files_result = await get_files_details_in_folder_by_path_chat_id_and_type(
            session = session,
            path    = path,
            chat_id = user_chat_id,
            type_id = type_id
        )

    if not files_result:
        return await inline_query.answer([]) 

    for id, (tg_ig, name) in enumerate(files_result):
        payload = {'id': f"file_{id}", id_param: tg_ig}
        # Telegram REQUIRES title for these types
        if file_ext in ('mp3', 'mp4', 'doc'):
            payload['title'] = f"{name}.{file_ext}"
        
        results.append(ResultClass(**payload))

    await inline_query.answer(
        results     = results,
        cache_time  = 0,
        is_personal = True
    )

@inline_router.inline_query(InlineSearchParser(target_type = "folders_list"))
async def handle_folder_list_search(inline_query: InlineQuery, parts: list):
    
    user_chat_id = inline_query.from_user.id
    path         = parts[0]

    results: List[InlineQueryResult] = []
    async with get_session() as session:

        folder = await get_folder_by_chat_id_and_path(
            session = session,
            chat_id = user_chat_id, 
            path    = path
        )

    if not folder or not folder.child_folders:
        empty_result = InlineQueryResultArticle(
            id                    = "empty",
            title                 = "Folder is empty",
            description           = f"No sub-folders found in: `{parts[0]}`",
            input_message_content = InputTextMessageContent(
                message_text      = "This folder has no sub-folders to show."
            )
        )
        return await inline_query.answer([empty_result])
    
    results = []
    for id, child_folder in enumerate(folder.child_folders):
        result = InlineQueryResultArticle(
            id                    = f"folder_{child_folder.id}_{id}",
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

    await inline_query.answer(
        results     = results,
        cache_time  = 0,
        is_personal = True
    )

@inline_router.inline_query(InlineSearchParser(target_type = "by_filetype"))
async def handle_search_by_filetype(inline_query: InlineQuery, parts: list):

    file_ext = parts[1]
    type_id = MEDIA_TYPE_ID_MAP.get(file_ext)
    
    if type_id is None:
        return await inline_query.answer([])

    user_chat_id = inline_query.from_user.id
    
    result_info = get_cached_result_class(file_ext)

    if result_info is None: 
        return await inline_query.answer([])
    
    ResultClass, id_param = result_info
    
    results: List[InlineQueryResult] = []
    async with get_session() as session:
        
        true_files = await get_files_by_type_and_chat_id(
            session = session,
            type_id = type_id,
            chat_id = user_chat_id
        )

    for f in true_files:
        payload = {'id': f"file_{f.id}", id_param: f.tg_id}
        # Telegram REQUIRES title for these types
        if file_ext in ('mp3', 'mp4', 'doc'):
            payload['title'] = f"File {f.file_name}.{file_ext}"
        
        results.append(ResultClass(**payload))

    await inline_query.answer(
        results     = results,
        cache_time  = 0,
        is_personal = True
    )

