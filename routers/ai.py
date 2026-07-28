from fastapi import APIRouter
from pydantic import BaseModel
from connection import config, model
from agents import Agent, Runner

router = APIRouter(prefix="/ai", tags=["AI"])

class AIQuery(BaseModel):
    query: str
    context: str = ""

@router.post("/chat")
async def ai_chat(request: AIQuery):
    try:
        agent = Agent(
            name="AI Assistant",
            instructions="You are a helpful assistant for an LMS platform.",
            model=model
        )
        result = await Runner.run(
            starting_agent=agent,
            input=f"Context: {request.context}. Question: {request.query}",
            run_config=config
        )
        return {"response": result.final_output}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}