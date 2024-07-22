from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    clear_history: bool = False
