from typing import Optional

from pydantic import BaseModel


class FileMessage(BaseModel):
    user_id: int
    action: str
    file_name: Optional[str] = None
