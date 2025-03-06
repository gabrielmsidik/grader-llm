from pydantic import BaseModel
from .enums import ReasonCode

class Critique(BaseModel):
    feedback: str
    reason_code: ReasonCode
