"""
Streaming LLM Response Handler using FastAPI with Server-Sent Events (SSE)
"""
import os
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Streaming LLM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Use AI Proxy (aipipe.org) if available, otherwise OpenAI
if AIPROXY_TOKEN:
    API_KEY = AIPROXY_TOKEN
    API_BASE = "https://aipipe.org/openai/v1"
else:
    API_KEY = OPENAI_API_KEY
    API_BASE = "https://api.openai.com/v1"


class PromptRequest(BaseModel):
    prompt: str
    stream: bool = True


async def stream_openai_response(prompt: str):
    """Stream response from OpenAI API using SSE format."""
    # Send immediate empty chunk with padding to flush proxy buffers
    padding = " " * 2048
    yield f'data: {{"choices": [{{"delta": {{"content": ""}}}}], "padding": "{padding}"}}\n\n'
    await asyncio.sleep(0)  # Force flush

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "stream": True,
        "max_tokens": 1000,
        "temperature": 0.7,
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{API_BASE}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f'data: {{"error": "API error: {response.status_code}"}}\n\n'
                    yield "data: [DONE]\n\n"
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        yield f"data: {data}\n\n"
                        
    except httpx.TimeoutException:
        yield 'data: {"error": "Request timed out"}\n\n'
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f'data: {{"error": "{str(e)}"}}\n\n'
        yield "data: [DONE]\n\n"


@app.post("/")
@app.post("/stream")
async def stream_llm_response(request: PromptRequest):
    """
    Stream LLM response using Server-Sent Events.
    
    Accepts:
    - prompt: The user's prompt text
    - stream: Boolean to enable streaming (default: true)
    
    Returns:
    - SSE stream with content chunks
    """
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API key not configured. Set OPENAI_API_KEY or AIPROXY_TOKEN."
        )
    
    if not request.stream:
        # Non-streaming request - still return in SSE format for consistency
        return StreamingResponse(
            stream_openai_response(request.prompt),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    return StreamingResponse(
        stream_openai_response(request.prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Streaming LLM API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
