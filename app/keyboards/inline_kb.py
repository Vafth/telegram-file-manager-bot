from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from ..db import *

builder = InlineKeyboardBuilder()

async def build_folder(folders_in_folder: list[Folder], files_in_folder: list[TrueFile], cur_folder_id: int): 
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row: list[InlineKeyboardButton] = []
    len_all_objects = len(folders_in_folder) + len(files_in_folder)
    row_len = 1 + (len_all_objects)//6
    
    label = "../"
    callback_data = json.dumps({"a": "u"}) 
    
    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])

    for i, folder in enumerate(folders_in_folder):
        label = f"/{folder.folder_name}/"
        callback_data = json.dumps({"a": "d", "f": folder.id})

        button = InlineKeyboardButton(text=label, callback_data=callback_data)
        row.append(button)
        
        if (i) % row_len == (row_len) - 1:
            keyboard.inline_keyboard.append(row)
            row = []
    
    keyboard.inline_keyboard.append(row)
    row = []

    for i, file in enumerate(files_in_folder):
        
        label = f"/{file.file_name}.{file.short_version}"
        callback_data = json.dumps({"a": "g", "f": file.id, "o": cur_folder_id})

        button = InlineKeyboardButton(text=label, callback_data=callback_data)
        row.append(button)
        
        if (i) % row_len == (row_len) - 1:
            keyboard.inline_keyboard.append(row)
            row = []
    keyboard.inline_keyboard.append(row)
    row = []

    label = "Add folder"
    callback_data = json.dumps({"a": "af", "fd_id": cur_folder_id})

    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])

    return keyboard


async def build_folder_legacy(folders_in_folder: list[Folder], files_in_folder: list[TrueFile], cur_folder_id: int, i: int = 2): 
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row: list[InlineKeyboardButton] = []
    
    label = "../"
    callback_data = json.dumps({"a": "u", "f": cur_folder_id}) 
    
    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])

    for i, folder in enumerate(folders_in_folder):
        label = f"/{folder.folder_name}/"
        callback_data = json.dumps({"a": "d", "f": folder.id})

        button = InlineKeyboardButton(text=label, callback_data=callback_data)
        row.append(button)
        
        if (i + 1) % 2 == 0 or i == len(folders_in_folder) - 1:
            keyboard.inline_keyboard.append(row)
            row = []

    for i, file in enumerate(files_in_folder):
        label = f"/{file.file_name}.{file.short_version}"
        callback_data = json.dumps({"a": "g", "f": file.id, "o": cur_folder_id})

        button = InlineKeyboardButton(text=label, callback_data=callback_data)
        row.append(button)
        
        if (i + 1) % 2 == 0 or i == len(files_in_folder) - 1:
            keyboard.inline_keyboard.append(row)
            row = []

    label = "Add folder"
    callback_data = json.dumps({"a": "af", "f": cur_folder_id})

    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])

    label = "Delete Folder"
    callback_data = json.dumps({"a": "dl", "f": cur_folder_id})

    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])

    return keyboard


async def delete_file_button(folder_id, file_id): 
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    label = "Delete File"
    callback_data = json.dumps({"a": "df", "f": file_id, "o": folder_id})

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=callback_data)]
    ])
    
    return keyboard

async def confirm_folder_deleting_button(): 
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    label = "Yes, Delete that folder"
    callback_data = json.dumps({"a": "cd", "c": True}) # confirm folder deleting
    
    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])
    
    label = "No, Cancel"
    callback_data = json.dumps({"a": "cd", "c": False}) # unconfirm folder deleting 
    
    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])

    return keyboard

async def confirm_file_moving_button(folder_id:int): 
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    label = f"Yes, move all files!"
    callback_data = json.dumps({"a": "cm", "c": True, "f": folder_id})
    
    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])
    
    label = "No, Cancel"
    callback_data = json.dumps({"a": "cm", "c": False, "f": folder_id})
    
    button = InlineKeyboardButton(text=label, callback_data=callback_data)
    keyboard.inline_keyboard.append([button])

    return keyboard
    