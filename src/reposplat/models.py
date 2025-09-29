
from pathlib import Path

from pydantic import BaseModel


class File(BaseModel):
    path: Path
    contents: str


class CombinedFiles(BaseModel):
    text: str
