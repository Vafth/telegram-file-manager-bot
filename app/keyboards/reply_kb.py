from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import json
from ..db import *

def build_reply_kb(key_labels: list[str], cols: int = 4, one_time: bool = True) -> ReplyKeyboardMarkup: 
    if not key_labels:
        return ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)  # Empty safe fallback
    
    builder = ReplyKeyboardBuilder()

    for i in range(0, len(key_labels), cols):
        row_labels = key_labels[i:i + cols]  # Slice for row
        row_buttons = [KeyboardButton(text=label) for label in row_labels]
        builder.row(*row_buttons)  # * unpacks for builder.row(btn1, btn2, ...)
    
    # Finalize with defaults: Resizable, persistent
    markup = builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=one_time,
    )
    return markup