from pydantic import BaseModel
from typing import List

class QuestionAnswerResponse(BaseModel):
    question: str
    actual_answer: str
    student_answer: str
    documents: List[str]
