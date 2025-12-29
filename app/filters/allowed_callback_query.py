from aiogram.filters import Filter
from aiogram.types import CallbackQuery

from typing import Union, Dict, Any
import json

class CallbackDataParser(Filter):
    def __init__(self, action: str):
        self.action = action
 
    async def __call__(self, callback: CallbackQuery) -> Union[bool, Dict[str, Any]]:
        
        data            = json.loads(callback.data)
        callback_action = data.get("a")
        
        callback_data: list[Union[int, bool, None]] = []

        if callback_action == "g": # get file
            callback_data.append(data.get("f")) # file id
            callback_data.append(data.get("o")) # current folder id
        
        elif callback_action == "d": # down folder to the target one
            callback_data.append(data.get("f")) # target folder id
        
        elif callback_action == "af": # Add folder
            callback_data.append(data.get("f")) # current folder id
            
        elif callback_action == "df": # Delete file
            callback_data.append(data.get("f")) # file id
            callback_data.append(data.get("o")) # current folder id
        
        elif callback_action == "cd": # Folder deleting confirmation 
            callback_data.append(data.get("c")) # confirm or not

        elif callback_action == "cm": # Files moving confirmation 
            callback_data.append(data.get("c")) # confirm or not
            callback_data.append(data.get("f")) # folder id
        
        elif callback_action == "u": # up folder to the parrent one
            callback_data.append(None)

        if callback_action == self.action:
            return {"callback_data": callback_data} # Return the data only if the type matches
        
        return False