# Deep Dive Debugging - "Failed to Fetch" Error

## Root Cause Analysis

The frontend is showing "It seems the connection was interrupted" which means:
- **Frontend is catching a "Failed to fetch" error**
- **Backend is NOT responding to requests**

## Possible Causes

### 1. Backend Not Running
- Check if backend server is actually running
- Check if it's running on the correct port (8000)
- Check for startup errors

### 2. Backend Crashing on Startup
- FAISS index loading might be failing
- Embedding model loading might be hanging
- Import errors
- Configuration errors

### 3. Backend Crashing on Request
- Retrieval initialization might be blocking
- LLM chain might be hanging
- Conversation memory might be causing issues

### 4. Network/CORS Issues
- CORS not configured properly
- Port mismatch between frontend and backend
- Firewall blocking requests

## How to Debug

### Step 1: Check if Backend is Running
```bash
cd backend
python main.py
```

Look for:
- ✅ "Application startup complete"
- ✅ "Uvicorn running on http://0.0.0.0:8000"
- ❌ Any error messages
- ❌ Hanging/freezing

### Step 2: Test Backend Directly
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok"}`

### Step 3: Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "hi"}'
```

Should return JSON with answer field.

### Step 4: Check Browser Console
Open browser DevTools (F12) → Console tab
- Look for network errors
- Look for CORS errors
- Check the actual error message

### Step 5: Check Backend Logs
When you send a request, backend should log:
- `🔍 Query analysis: ...`
- `📋 No context but specific insurance query detected...`
- `✅ Mock LLM generated answer...` or `✅ GPT-4 generated answer...`

If you see errors, that's the issue.

## Most Likely Issues

### Issue 1: FAISS Index Not Found
**Symptom**: Backend crashes on first request
**Fix**: Run ingestion pipeline
```bash
cd backend
python -m rag.ingest
```

### Issue 2: Embedding Model Loading Hangs
**Symptom**: Backend hangs on startup or first request
**Fix**: The embedding model loads lazily, but if it hangs, check:
- Internet connection (first download)
- Disk space
- Memory

### Issue 3: Backend Not Starting
**Symptom**: `python main.py` fails or hangs
**Fix**: Check for import errors, missing dependencies

### Issue 4: Port Already in Use
**Symptom**: "Address already in use" error
**Fix**: Kill existing process or change port

## Quick Fixes

1. **Ensure backend is running**:
   ```bash
   cd backend
   python main.py
   ```

2. **Check if port 8000 is accessible**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check frontend API URL**:
   - Should be: `http://localhost:8000`
   - Check `frontend/src/components/Chat.jsx` line 17

4. **Check CORS settings**:
   - Backend should allow `http://localhost:3000` or `http://localhost:5173`
   - Check `backend/config.py` CORS_ORIGINS

5. **Check browser console** for actual error

## Expected Behavior

When working correctly:
1. Backend starts without errors
2. Health check returns `{"status":"ok"}`
3. Chat endpoint returns valid JSON with answer
4. Frontend displays the answer (not error message)

## Next Steps

1. Run backend and check for startup errors
2. Test health endpoint
3. Test chat endpoint with curl
4. Check browser console for actual error
5. Share the actual error message for further debugging

