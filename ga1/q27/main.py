"""
AI Security: Prompt Injection + Spam Detection + Output Sanitization
Production-ready version for Railway deployment.
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
# Logging Configuration
# =============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
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
# Request / Response Models
# =============================
class ValidationRequest(BaseModel):
    userId: str
    input: str
    category: str = "Prompt Injection"


class ValidationResponse(BaseModel):
    blocked: bool
    reason: str
    sanitizedOutput: Optional[str] = None
    confidence: float


# =============================
# Prompt Injection Patterns
# =============================
PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?(previous )?instructions",
    r"developer mode",
    r"act as",
    r"you are now",
    r"override (the )?system",
    r"reveal (your )?system prompt",
    r"show hidden instructions",
    r"jailbreak",
    r"bypass safety",
    r"pretend to be",
    r"disable safety",
    r"system prompt",
    r"switch to admin",
]

def detect_prompt_injection(text: str) -> Tuple[bool, float, str]:
    text_lower = text.lower()
    matches = 0

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            matches += 1

    if matches > 0:
        confidence = min(1.0, 0.9 + matches * 0.03)
        return True, confidence, "Prompt injection attempt detected"

    return False, 0.0, "No prompt injection detected"


# =============================
# Spam Detection (Your Logic Simplified)
# =============================
SPAM_KEYWORDS = [
    "lottery", "bitcoin", "crypto", "investment opportunity",
    "make money", "win prize", "click here", "limited offer"
]

def detect_spam(text: str) -> Tuple[bool, float, str]:
    text_lower = text.lower()
    matches = sum(1 for word in SPAM_KEYWORDS if word in text_lower)

    if matches > 1:
        confidence = min(1.0, 0.75 + matches * 0.05)
        return True, confidence, "Spam patterns detected"

    return False, 0.0, "No spam detected"


# =============================
# Output Sanitization (XSS Safe)
# =============================
def sanitize_output(text: str) -> str:
    sanitized = html.escape(text)
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'on\w+=".*?"', '', sanitized, flags=re.IGNORECASE)
    return sanitized


# =============================
# Rate Limiting (Basic Memory-Based)
# =============================
RATE_LIMIT = {}
MAX_REQUESTS = 20  # per session

def check_rate_limit(user_id: str):
    RATE_LIMIT[user_id] = RATE_LIMIT.get(user_id, 0) + 1
    if RATE_LIMIT[user_id] > MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests"
        )


# =============================
# Validation Endpoint
# =============================
@app.post("/validate", response_model=ValidationResponse)
async def validate_input(request: ValidationRequest):

    try:
        # Category enforcement
        if request.category != "Prompt Injection":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )

        # Rate limit check
        check_rate_limit(request.userId)

        if not request.input.strip():
            return ValidationResponse(
                blocked=False,
                reason="Empty input",
                sanitizedOutput="",
                confidence=0.0
            )

        # 1️⃣ Prompt Injection Detection (Primary)
        pi_blocked, pi_conf, pi_reason = detect_prompt_injection(request.input)
        if pi_blocked:
            logger.warning(f"PROMPT INJECTION BLOCKED | userId={request.userId}")
            return ValidationResponse(
                blocked=True,
                reason=pi_reason,
                sanitizedOutput=None,
                confidence=round(pi_conf, 2)
            )

        # 2️⃣ Spam Detection (Secondary)
        spam_blocked, spam_conf, spam_reason = detect_spam(request.input)
        if spam_blocked:
            logger.warning(f"SPAM BLOCKED | userId={request.userId}")
            return ValidationResponse(
                blocked=True,
                reason=spam_reason,
                sanitizedOutput=None,
                confidence=round(spam_conf, 2)
            )

        # 3️⃣ Sanitize Safe Output
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation error occurred"
        )


# =============================
# Health Endpoints
# =============================
@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# =============================
# Railway-Compatible Runner
# =============================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
