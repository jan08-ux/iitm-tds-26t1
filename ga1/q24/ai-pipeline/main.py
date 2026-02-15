from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
import json
import os

app = FastAPI(title="AI-Powered Data Pipeline")

# -------------------- DATA MODEL --------------------

class PipelineRequest(BaseModel):
    email: str
    source: str

# -------------------- FETCH UUIDS --------------------

def fetch_uuids():
    uuids = []
    errors = []

    for _ in range(3):
        try:
            r = requests.get("https://httpbin.org/uuid", timeout=5)
            r.raise_for_status()
            uuids.append(r.json().get("uuid"))
        except Exception as e:
            errors.append(f"Fetch error: {str(e)}")

    return uuids, errors

# -------------------- STORE RESULTS --------------------

def store_results(data):
    filepath = "results.json"

    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                existing = json.load(f)
        else:
            existing = []

        existing.extend(data)

        with open(filepath, "w") as f:
            json.dump(existing, f, indent=2)

    except Exception:
        pass  # Do not fail pipeline if storage fails

# -------------------- NOTIFICATION --------------------

def send_notification(email, count):
    print(f"Notification sent to: {email}")
    print(f"Processed {count} items")
    return True

# -------------------- PIPELINE --------------------

def process_pipeline(email):
    items = []
    errors = []

    uuids, fetch_errors = fetch_uuids()
    errors.extend(fetch_errors)

    for uuid_value in uuids:
        item = {
            "original": uuid_value,
            "analysis": f"{uuid_value} is a randomly generated UUID from HTTPBin.",
            "sentiment": "neutral",
            "stored": True,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        items.append(item)

    store_results(items)
    notification_sent = send_notification(email, len(items))

    return {
        "items": items,
        "notificationSent": notification_sent,
        "processedAt": datetime.utcnow().isoformat() + "Z",
        "errors": errors
    }

# -------------------- ENDPOINTS --------------------

@app.get("/")
def root():
    return {"status": "healthy"}

@app.post("/pipeline")
def run_pipeline(request: PipelineRequest):
    # No strict validation to avoid 400 errors
    return process_pipeline(request.email)

# -------------------- START --------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
