from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from openai import OpenAI
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI-Powered Data Pipeline")

# ---------------------- OPENAI CLIENT ----------------------

def get_client():
    token = os.getenv("AIPIPE_TOKEN")
    if not token:
        raise RuntimeError("AIPIPE_TOKEN not set")
    return OpenAI(
        api_key=token,
        base_url="https://aipipe.org/openai/v1"
    )

# ---------------------- DATA MODEL ----------------------

class PipelineRequest(BaseModel):
    email: str
    source: str

# ---------------------- FETCH UUID ----------------------

def fetch_uuids():
    results = []
    errors = []

    for i in range(3):
        try:
            response = requests.get("https://httpbin.org/uuid", timeout=10)
            response.raise_for_status()
            results.append(response.json()["uuid"])
        except Exception as e:
            errors.append(f"Fetch error: {str(e)}")

    return results, errors

# ---------------------- AI ANALYSIS ----------------------

def analyze_with_ai(uuid_value):
    try:
        client = get_client()

        prompt = f"""
Analyze this UUID value.
1. Provide a short 1-2 sentence explanation.
2. Classify sentiment as positive, negative, or neutral.

UUID:
{uuid_value}

Respond exactly in this format:
Summary: <text>
Sentiment: <positive/negative/neutral>
"""

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )

        text = response.choices[0].message.content.strip()

        summary = "Analysis unavailable"
        sentiment = "neutral"

        for line in text.split("\n"):
            if line.startswith("Summary:"):
                summary = line.replace("Summary:", "").strip()
            if line.startswith("Sentiment:"):
                sentiment = line.replace("Sentiment:", "").strip().lower()

        return summary, sentiment

    except Exception as e:
        return "Analysis unavailable due to error", "neutral"

# ---------------------- STORAGE ----------------------

def store_result(original, analysis, sentiment):
    filepath = "results.json"

    result = {
        "original": original,
        "analysis": analysis,
        "sentiment": sentiment,
        "stored": True,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(result)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    except Exception:
        result["stored"] = False

    return result

# ---------------------- NOTIFICATION ----------------------

def send_notification(email, count):
    print(f"Notification sent to: {email}")
    print(f"Processed {count} UUIDs")
    return True

# ---------------------- PIPELINE ----------------------

def process_pipeline(email):
    items = []
    errors = []

    uuids, fetch_errors = fetch_uuids()
    errors.extend(fetch_errors)

    for uuid_value in uuids:
        try:
            analysis, sentiment = analyze_with_ai(uuid_value)
            stored = store_result(uuid_value, analysis, sentiment)
            items.append(stored)
        except Exception as e:
            errors.append(str(e))

    notification_sent = send_notification(email, len(items))

    return {
        "items": items,
        "notificationSent": notification_sent,
        "processedAt": datetime.utcnow().isoformat() + "Z",
        "errors": errors
    }

# ---------------------- ENDPOINTS ----------------------

@app.get("/")
def root():
    return {"status": "healthy"}

@app.post("/pipeline")
def run_pipeline(request: PipelineRequest):

    if request.source != "HTTPBin UUID":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Expected 'HTTPBin UUID', got '{request.source}'"
        )

    return process_pipeline(request.email)

# ---------------------- START ----------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
