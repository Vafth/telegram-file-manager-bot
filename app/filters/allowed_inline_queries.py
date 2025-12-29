from aiogram.filters import Filter
from aiogram.types import InlineQuery
from aiogram import  Bot

from typing import Union, Dict, Any

class inlineUserIsAllowed(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, inline_query: InlineQuery, bot: Bot) -> bool:
        return inline_query.from_user.id in bot.my_admin_list
    
class InlineSearchParser(Filter):
    def __init__(self, target_type: str):
        self.target_type = target_type
 
    async def __call__(self, inline_query: InlineQuery) -> Union[bool, Dict[str, Any]]:
        
        query_text = inline_query.query.strip()
        if not query_text:
            return {"search_type": "help", "args": []}
        
        queries = query_text.split(".")

        if not queries: stype = "help"
        elif len(queries) == 2: stype = 'in_folder' if queries[0] != "" else 'by_filetype'
        else: stype = 'folders_list'

        if stype == self.target_type:
            return {"parts": queries} # Return the data only if the type matches
        
        return False