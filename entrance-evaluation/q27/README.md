# Q27: Local Ollama Endpoint Setup

## Task

Set up a local AI server using Ollama and expose it to the internet via ngrok with proper CORS configuration and custom headers for remote access and verification.

---

## Requirements

* Run Ollama locally on port 11434
* Enable CORS to allow cross-origin requests from any origin
* Expose the local server via ngrok tunnel with public HTTPS URL
* Inject custom `X-Email` header in all responses
* Configure proper CORS headers for browser compatibility
* Submit the public ngrok URL for grading

---

## Approach

### 1. Install Ollama
Download and install Ollama to run AI models locally on your machine.

### 2. Download AI Model
Pull a lightweight model suitable for your system's memory constraints.

### 3. Configure CORS
Set environment variable to allow cross-origin requests before starting the server.

### 4. Start Ollama Server
Run Ollama with CORS enabled on localhost:11434.

### 5. Install and Configure ngrok
Set up ngrok to create a secure tunnel from internet to localhost.

### 6. Create Public Tunnel
Run ngrok with custom headers to expose Ollama publicly.

### 7. Verify Setup
Test the public URL to ensure proper connectivity and header injection.

---

## Installation Steps

### Install Ollama

**Download:**
Visit [ollama.com/download](https://ollama.com/download) and download the Windows installer.

**Verify Installation:**
```powershell
ollama --version
```

**Expected Output:**
```
ollama version is 0.13.5
```

### Download AI Model

**Initial Attempt (Failed - Memory Issue):**
```powershell
ollama pull gemma3:1b-it-qat
```

**Error:**
```
Error: 500 Internal Server Error: model requires more system memory (1.6 GiB) than is available (1.3 GiB)
```

**Solution - Use Smaller Model:**
```powershell
ollama pull qwen2.5:0.5b
```

**Verify Model:**
```powershell
ollama list
```

**Output:**
```
NAME                ID              SIZE      MODIFIED
qwen2.5:0.5b        a8b0c5157701    397 MB    2 minutes ago
```

**Test Model:**
```powershell
ollama run qwen2.5:0.5b "What is 2+2?"
```

**Output:**
```
When you ask me "What is 2 + 2?", I can only provide an exact numeric answer to your question.
2 + 2 = 4
...
```

### Install ngrok

**Download:**
Visit [ngrok.com/download](https://ngrok.com/download) and download Windows version.

**Extract:**
Extract `ngrok.exe` to `C:\ngrok\`

**Get Authtoken:**
Sign up at [ngrok.com](https://ngrok.com) and get authtoken from [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)

**Configure ngrok:**
```powershell
C:\ngrok\ngrok.exe config add-authtoken 38VKzJPdTrJpw2VZO5akwB2cdWN_PbXWeF6xwmp4DSkt74gW
```

**Output:**
```
Authtoken saved to configuration file: C:\Users\...\ngrok.yml
```

---

## Execution

### Start Ollama Server (Terminal Window 1)

**Set CORS Environment Variable:**
```powershell
$env:OLLAMA_ORIGINS="*"
```

**Start Server:**
```powershell
ollama serve
```

**Issue Encountered:**
```
Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address (protocol/network address/port) is normally permitted.
```

**Cause:** Ollama was already running as a background service.

**Solution:** Use the existing running instance. Verify it works:
```powershell
curl http://localhost:11434/api/tags -UseBasicParsing
```

**Expected Output:**
```
StatusCode        : 200
Content           : {"models":[{"name":"qwen2.5:0.5b","model":"qwen2.5:0.5b",...}]}
```

### Start ngrok Tunnel (Terminal Window 2)

**Create Public Tunnel:**
```powershell
C:\ngrok\ngrok.exe http 11434 --response-header-add "X-Email: 23f3003225@ds.study.iitm.ac.in" --response-header-add "Access-Control-Expose-Headers: *" --response-header-add "Access-Control-Allow-Headers: Ngrok-skip-browser-warning" --host-header=localhost
```

**Expected Output:**
```
ngrok                                                                         (Ctrl+C to quit)

Session Status                online
Account                       23f3003225@ds.study.iitm.ac.in (Plan: Free)
Version                       3.35.0
Region                        India (in)
Latency                       43ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://lanate-kareen-photostatically.ngrok-free.dev -> http://localhost:11434

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Note:** Keep this terminal window open throughout the session.

---

## Verification

### Test Local Connection

**Check Ollama Locally:**
```powershell
curl http://localhost:11434/api/version -UseBasicParsing
```

**Expected Response:**
```json
{"version":"0.5.8"}
```

### Test Public URL

**Check ngrok Tunnel:**
```powershell
curl https://lanate-kareen-photostatically.ngrok-free.dev/api/version -UseBasicParsing
```

**Expected Response:**
```json
{"version":"0.5.8"}
```

### Monitor Connections

**ngrok Interface Shows Activity:**
```
HTTP Requests
-------------
09:26:35.000 IST OPTIONS /api/version           204 No Content
09:26:35.366 IST OPTIONS /api/version           204 No Content
```

These OPTIONS requests are CORS preflight checks from the grading system, confirming proper setup.

---

## Common Issues and Solutions

### Issue 1: Memory Constraints

**Problem:**
```
Error: model requires more system memory (1.6 GiB) than is available (1.3 GiB)
```

**Cause:** The `gemma3:1b-it-qat` model requires 1.6 GB RAM but only 1.3 GB was available.

**Solution:**
Switch to a smaller model:
```powershell
ollama pull qwen2.5:0.5b  # Only ~400 MB
```

**Available Models by Size:**
* `qwen2.5:0.5b` - 397 MB (recommended for <2 GB RAM)
* `gemma3:1b-it-qat` - 1.0 GB (requires ~1.6 GB RAM)
* `llama3` - Larger models (requires 4+ GB RAM)

### Issue 2: Port Already in Use

**Problem:**
```
Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address (protocol/network address/port) is normally permitted.
```

**Cause:** Ollama is already running as a background service.

**Solution:**
The server is already running. Either:
* Use the existing instance (proceed to ngrok setup)
* Stop the service via Task Manager (`Ctrl+Shift+Esc` → End "Ollama" task) and restart with CORS enabled

### Issue 3: CORS Headers Missing

**Problem:** Assignment checker reports CORS errors or "Failed to fetch".

**Cause:** `OLLAMA_ORIGINS` environment variable not set before starting Ollama.

**Solution:**
1. Stop Ollama (Task Manager → End Task on "Ollama")
2. In PowerShell: `$env:OLLAMA_ORIGINS="*"`
3. Start Ollama: `ollama serve`
4. **Critical:** Set the variable in the same PowerShell session before running `ollama serve`

### Issue 4: PowerShell Header Syntax Error

**Problem:**
```
Cannot bind parameter 'Headers'. Cannot convert the "ngrok-skip-browser-warning: true" value...
```

**Cause:** Bash-style `-H` flag doesn't work in PowerShell.

**Solution:**
Use PowerShell syntax:
```powershell
curl https://YOUR-URL.ngrok-free.app/api/version -Headers @{"ngrok-skip-browser-warning"="true"} -UseBasicParsing
```

Or test without the header:
```powershell
curl https://YOUR-URL.ngrok-free.app/api/version -UseBasicParsing
```

---

## Implementation Details

### Architecture

**Request Flow:**
```
Internet → ngrok Tunnel → localhost:11434 → Ollama Server
```

**Response Flow:**
```
Ollama Server → ngrok (injects headers) → Internet
```

### Tools

* **Ollama:** Local LLM server for running AI models
* **ngrok:** Secure tunnel service for exposing localhost to internet
* **Model:** qwen2.5:0.5b (397 MB, lightweight alternative to gemma3:1b-it-qat)

### Configuration Parameters

**CORS Configuration:**
* `OLLAMA_ORIGINS="*"` - Allows requests from any origin
* Essential for web browser access and grading system

**ngrok Flags:**
* `--response-header-add "X-Email: 23f3003225@ds.study.iitm.ac.in"` - Identifies submission for grading
* `--response-header-add "Access-Control-Expose-Headers: *"` - Allows JavaScript to read all headers
* `--response-header-add "Access-Control-Allow-Headers: Ngrok-skip-browser-warning"` - Permits custom header to bypass ngrok warning page
* `--host-header=localhost` - Ensures Ollama sees requests as from localhost (prevents 403 errors)

### Why Each Component is Needed

**CORS (Cross-Origin Resource Sharing):**
Allows web browsers to make requests from different domains. Without it, browsers block the requests due to security policies.

**Custom Headers:**
* `X-Email`: Identifies your submission for the grading system
* CORS headers: Enable browser-based access to the API
* `host-header=localhost`: Prevents Ollama from rejecting proxied requests

**ngrok:**
Creates a secure HTTPS tunnel so the grading system can access your local Ollama instance without exposing your entire network.

**Smaller Model:**
Using `qwen2.5:0.5b` instead of `gemma3:1b-it-qat` allows the setup to work on systems with limited RAM (< 2 GB available).

---

## Submission

**Copy Your ngrok URL:**
```
https://lanate-kareen-photostatically.ngrok-free.dev
```

**Submit:**
Paste the HTTPS forwarding URL into the assignment submission box.

**Keep Running:**
Both Ollama and ngrok must remain running until grading is complete.

---

## Clean Up

**Stop Services:**
Press `Ctrl+C` in the ngrok terminal window.

**Stop Ollama:**
Task Manager (`Ctrl+Shift+Esc`) → End "Ollama" task

**Uninstall Ollama (Optional):**
Windows Settings → Apps → Add or Remove Programs → Ollama → Uninstall

**Remove Model Files (Optional):**
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.ollama"
```
This frees up ~400 MB of disk space.

**Remove ngrok (Optional):**
```powershell
Remove-Item -Recurse -Force "C:\ngrok"
```

---

## Summary

This setup demonstrates:
* Running local AI models with Ollama (using qwen2.5:0.5b for memory efficiency)
* Exposing local servers securely to the internet with ngrok
* Configuring CORS for web API access
* Injecting custom HTTP headers for verification
* Managing environment variables for service configuration
* Troubleshooting memory constraints by selecting appropriate model sizes

**Final Result:** A publicly accessible AI API endpoint (`https://lanate-kareen-photostatically.ngrok-free.dev`) running the qwen2.5:0.5b model on your local machine, accessible from anywhere on the internet with proper CORS and custom headers.
