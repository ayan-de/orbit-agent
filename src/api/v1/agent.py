from fastapi import APIRouter

router = APIRouter()

@router.post("/invoke")
async def invoke_agent():
    return {"message": "Agent invocation placeholder"}
