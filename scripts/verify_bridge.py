import asyncio
import sys
import os
import uvicorn
from fastapi import FastAPI, Body

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.bridge.client import BridgeClient, BridgeCommandResponse

# Mock Bridge Server
mock_app = FastAPI()

@mock_app.post("/api/v1/commands/execute")
async def execute_mock_command(payload: dict = Body(...)):
    print(f"Mock Bridge received: {payload}")
    cmd = payload.get("command")
    args = payload.get("args", [])
    
    if cmd == "ls":
        return {
            "stdout": "file1.txt\nfile2.py",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 10
        }
    elif cmd == "fail":
        return {
            "stdout": "",
            "stderr": "Command failed intentionally",
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

async def run_client_test():
    # Wait for server to start
    await asyncio.sleep(2)
    
    print("\n--- Testing Bridge Client ---")
    client = BridgeClient(base_url="http://localhost:3001")
    
    try:
        print("1. Testing 'ls' command...")
        res = await client.list_files()
        print(f"✅ Result: {res.stdout.strip()} (Exit Code: {res.exit_code})")
        
        print("\n2. Testing 'echo' command...")
        res = await client.execute_command("echo", ["Hello Bridge"])
        print(f"✅ Result: {res.stdout.strip()}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        await client.close()

async def main():
    # Run server and client concurrently
    server_task = asyncio.create_task(start_mock_server())
    client_task = asyncio.create_task(run_client_test())
    
    # Wait for client tests to finish
    await client_task
    
    # Cancel server (clean up)
    server_task.cancel() # or just exit

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
