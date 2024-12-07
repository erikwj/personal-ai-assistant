from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService
import logging
import json
from pydantic import BaseModel

app = FastAPI(title="LLM Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Initialize LLM service
    llm_service = LLMService()
except FileNotFoundError as e:
    logging.error(str(e))
    llm_service = None

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Welcome to LLM Assistant API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": llm_service is not None
    }

async def generate_stream(request: ChatRequest):
    try:
        async for text in llm_service.generate_response_stream(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        ):
            yield f"data: {json.dumps({'text': text})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if llm_service is None:
        raise HTTPException(
            status_code=503,
            detail="LLM model not loaded. Please check server logs for details."
        )
    
    return StreamingResponse(
        generate_stream(request),
        media_type="text/event-stream"
    )

@app.post("/prompt", response_model=PromptResponse)
async def process_prompt(request: PromptRequest):
    try:
        response = await llm_service.process_prompt(request.prompt)
        return PromptResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 