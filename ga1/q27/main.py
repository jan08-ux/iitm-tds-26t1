"""
AI Security Validation API
Prompt Injection Detection + Output Sanitization
Railway Compatible
"""

import re
import os
import html
import logging
from typing import Optional, Tuple
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =============================
# Logging
# =============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================
# FastAPI App
# =============================
app = FastAPI(title="AI Security Validation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================
# Models
# =============================
class ValidationRequest(BaseModel):
    userId: str
    input: str
    category: str


class ValidationResponse(BaseModel):
    blocked: bool
    reason: str
    sanitizedOutput: Optional[str] = None
    confidence: float


# =============================
# Prompt Injection Detection
# =============================
PROMPT_PATTERNS = [
    r"\bignore\b.*\binstructions\b",
    r"\bdeveloper mode\b",
    r"\bact as\b",
    r"\byou are now\b",
    r"\boverride\b",
    r"\breveal\b.*\bprompt\b",
    r"\bsystem prompt\b",
    r"\bjailbreak\b",
    r"\bbypass\b",
    r"\bdisable safety\b",
]

def detect_prompt_injection(text: str) -> Tuple[bool, float]:
    text_lower = text.lower()
    matches = sum(1 for p in PROMPT_PATTERNS if re.search(p, text_lower))
    if matches > 0:
        confidence = min(1.0, 0.85 + matches * 0.05)
        return True, confidence
    return False, 0.0


# =============================
# Output Sanitization (XSS Safe)
# =============================
def sanitize_output(text: str) -> str:
    return html.escape(text)


# =============================
# Validation Endpoint
# Accept BOTH "/" and "/validate"
# =============================
@app.post("/", response_model=ValidationResponse)
@app.post("/validate", response_model=ValidationResponse)
async def validate_input(request: ValidationRequest):

    try:
        # Normalize category check
        if request.category.lower().strip() != "prompt injection":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )

        if not request.input.strip():
            return ValidationResponse(
                blocked=False,
                reason="Empty input",
                sanitizedOutput="",
                confidence=0.0
            )

        # Prompt Injection Detection
        blocked, confidence = detect_prompt_injection(request.input)

        if blocked:
            logger.warning(f"Prompt injection blocked | userId={request.userId}")
            return ValidationResponse(
                blocked=True,
                reason="Prompt injection attempt detected",
                sanitizedOutput=None,
                confidence=round(confidence, 2)
            )

        # Safe input
        sanitized = sanitize_output(request.input)

        return ValidationResponse(
            blocked=False,
            reason="Input passed all security checks",
            sanitizedOutput=sanitized,
            confidence=0.95
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Internal validation error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal validation error"
        )


# =============================
# Health Check
# =============================
@app.get("/")
async def health():
    return {"status": "ok"}


# =============================
# Railway Runner
# =============================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
