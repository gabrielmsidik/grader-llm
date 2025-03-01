from enum import Enum

class ReasonCode(str, Enum):
    CORRECT = "CORRECT"
    SOURCE_CORRECT = "SOURCE_CORRECT"
    HALLUCINATION = "HALLUCINATION"
    INVALID_INPUT = "INVALID_INPUT"
    IDK = "IDK"
