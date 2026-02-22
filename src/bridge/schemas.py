from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class BridgeCommandRequest(BaseModel):
    command: str
    args: List[str] = []
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 30000  # ms
    trusted: bool = False  # Skip injection check for internal tools


class BridgeCommandResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class BridgeError(BaseModel):
    message: str
    code: str
