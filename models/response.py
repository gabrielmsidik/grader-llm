from pydantic import BaseModel
from .enums import ReasonCode

class Critique(BaseModel):
    score: float
    feedback: str
    reason_code: ReasonCode
