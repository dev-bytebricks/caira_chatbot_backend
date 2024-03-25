from enum import Enum
from pydantic import BaseModel

class Mode(Enum):
    NA = 0
    Simplify = 1
    Elaborate = 2
    Get_Legal_Precedent = 3

class AiRequest(BaseModel):
    user_msg: str
    traceless: bool
    mode: Mode