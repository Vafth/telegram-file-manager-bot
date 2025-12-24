from pydantic import BaseModel
from typing import Optional

class TrueFile(BaseModel):
    id:        Optional[int]
    file_name: str
    tg_id:     str
    backup_id: int
    short_version: str