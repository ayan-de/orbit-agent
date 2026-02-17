import httpx
import logging
from typing import Dict, Any, Optional

from src.config import settings
from src.bridge.schemas import BridgeCommandRequest, BridgeCommandResponse

logger = logging.getLogger("orbit.bridge")

class BridgeClient:
    """Client for communicating with the NestJS Bridge service."""
    
    def __init__(self, base_url: str = settings.BRIDGE_URL, api_key: str = settings.BRIDGE_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
        )

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def execute_command(self, cmd: str, args: list = None, cwd: str = None) -> BridgeCommandResponse:
        """
        Execute a shell command via the Bridge.
        """
        if args is None:
            args = []
            
        payload = BridgeCommandRequest(
            command=cmd,
            args=args,
            cwd=cwd
        )
        
        try:
            logger.info(f"Executing command via bridge: {cmd} {args}")
            response = await self.client.post("/api/v1/commands/execute", json=payload.model_dump())
            
            response.raise_for_status()
            data = response.json()
            
            return BridgeCommandResponse(**data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Bridge HTTP Error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Bridge command failed: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"Bridge Request Error: {e}")
            raise Exception(f"Failed to connect to Bridge: {e}") from e

    async def list_files(self, path: str = ".") -> BridgeCommandResponse:
        """Helper to list files in a directory."""
        return await self.execute_command("ls", ["-la", path])

    async def read_file(self, path: str) -> BridgeCommandResponse:
        """Helper to read a file."""
        return await self.execute_command("cat", [path])

# Global instance
bridge_client = BridgeClient()
