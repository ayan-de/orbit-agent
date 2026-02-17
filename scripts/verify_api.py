import asyncio
import sys
import os
import httpx
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.main import app

async def run_api_test():
    # Wait for server to start
    await asyncio.sleep(2)
    
    print("\n--- Testing Agent API ---")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Health Check
        print("1. Testing Health Check...")
        res = await client.get("/api/v1/health/")
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        
        # 2. Invoke Agent
        print("\n2. Testing /agent/invoke (Question)...")
        payload = {"message": "What is Python?", "session_id": "test", "user_id": "test_user"}
        res = await client.post("/api/v1/agent/invoke", json=payload, timeout=60.0)
        
        if res.status_code == 200:
            data = res.json()
            print(f"✅ Success!")
            print(f"Intent: {data.get('intent')}")
            print(f"Answer: {data.get('messages')[0]}")
        else:
            print(f"❌ Failed: {res.status_code} - {res.text}")

async def main():
    config = uvicorn.Config(app, port=8000, log_level="error")
    server = uvicorn.Server(config)
    
    server_task = asyncio.create_task(server.serve())
    test_task = asyncio.create_task(run_api_test())
    
    await test_task
    # Force exit or cancel
    server.should_exit = True
    await server_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
