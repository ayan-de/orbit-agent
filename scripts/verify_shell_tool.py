import asyncio
import sys
import os
import uvicorn
from fastapi import FastAPI, Body

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.tools.shell import ShellTool

# Mock Bridge Server (same as before)
mock_app = FastAPI()

@mock_app.post("/api/v1/commands/execute")
async def execute_mock_command(payload: dict = Body(...)):
    print(f"Mock Bridge received: {payload}")
    cmd = payload.get("command")
    args = payload.get("args", [])
    
    if cmd == "ls" and "-la" in args:
        return {
            "stdout": "total 0\n-rw-r--r-- 1 user 1024 Jan 1 file.txt",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 10
        }
    elif cmd == "fail":
        return {
            "stdout": "",
            "stderr": "Command failed",
            "exit_code": 1,
            "duration_ms": 5
        }
    return {
        "stdout": f"Executed: {cmd} {' '.join(args)}",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 20
    }

async def start_mock_server():
    config = uvicorn.Config(mock_app, port=3001, log_level="error")
    server = uvicorn.Server(config)
    await server.serve()

async def run_tool_test():
    await asyncio.sleep(2)
    print("\n--- Testing Shell Tool ---")
    
    tool = ShellTool()
    
    try:
        print("1. Testing 'ls -la' command via Tool...")
        result = await tool.ainvoke({"command": "ls -la"})
        print(f"✅ Result:\n{result}")
        
        print("\n2. Testing 'echo hello' via Tool...")
        result = await tool.ainvoke({"command": "echo hello"})
        print(f"✅ Result:\n{result}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

async def main():
    server_task = asyncio.create_task(start_mock_server())
    client_task = asyncio.create_task(run_tool_test())
    
    await client_task
    server_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
