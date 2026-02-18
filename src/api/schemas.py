from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class AgentRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_id: str = "user"

class AgentResponse(BaseModel):
    messages: List[str]
    intent: str
    command: str = ""
    status: str
