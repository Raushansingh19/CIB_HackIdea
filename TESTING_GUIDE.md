# Testing Guide - How to Test the Chatbot Locally

## Prerequisites

1. **Backend Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Frontend Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

3. **FAISS Index** (if not exists):
   ```bash
   cd backend
   python -m rag.ingest
   ```

## Step-by-Step Testing

### 1. Start Backend Server

```bash
cd backend
python main.py
```

**Expected Output**:
```
============================================================
🚀 Insurance Chatbot Backend
============================================================
📍 Server will run on: http://0.0.0.0:8000
🔧 LLM Model: gpt-4
🌐 CORS Origins: ['http://localhost:3000', 'http://localhost:5173']
📁 Vector Store: data/vector_store
============================================================
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**If you see errors**:
- Check if port 8000 is already in use
- Check if FAISS index exists in `backend/data/vector_store/`
- Check Python dependencies are installed

### 2. Test Backend Health Endpoint

In a new terminal:
```bash
curl http://localhost:8000/health
```

**Expected Output**: `{"status":"ok"}`

### 3. Test Backend Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need health insurance for 57 year old male"}'
```

**Expected Output**: JSON with:
- `answer`: Detailed health insurance advice (not generic message)
- `policy_suggestions`: Array of suggestions
- `sources`: Array of source chunks
- `session_id`: Session ID for conversation

### 4. Start Frontend

In a new terminal:
```bash
cd frontend
npm run dev
```

**Expected Output**: 
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 5. Test in Browser

1. Open `http://localhost:5173` (or the port shown)
2. Open Browser DevTools (F12) → Console tab
3. Try these test queries:

**Test 1: Greeting**
- Input: "Hi"
- Expected: Friendly greeting, not generic error

**Test 2: Health Insurance Query**
- Input: "I need health insurance for 57 year old male"
- Expected: Detailed health insurance advice with:
  - Age-specific considerations
  - Coverage types
  - Follow-up questions
  - NOT: "I'm here to help" or generic message

**Test 3: Bike Insurance Query**
- Input: "I need bike insurance"
- Expected: Detailed bike insurance advice with:
  - Coverage types (motorcycle vs bicycle)
  - Key considerations
  - Follow-up questions

**Test 4: Comparison Query**
- Input: "compare different policies"
- Expected: Asks what type to compare

## Troubleshooting

### Issue: "Failed to fetch" Error

**Check**:
1. Is backend running? (Check terminal where you ran `python main.py`)
2. Is backend on port 8000? (Check startup logs)
3. Check browser console for actual error
4. Check CORS settings match frontend port

**Fix**:
- Ensure backend is running
- Check `frontend/src/components/Chat.jsx` line 17: `API_BASE_URL` should be `http://localhost:8000`
- Check `backend/config.py` CORS_ORIGINS includes your frontend port

### Issue: Generic "I'm here to help" Messages

**Check Backend Logs**:
- Look for: `🔍 Query analysis: ...`
- Look for: `📋 No context but specific insurance query detected...`
- Look for: `⚠️ Detected generic response...`

**Fix**:
- Backend should detect insurance queries and use fallback
- Check if `_default_fallback` is being called
- Verify query detection logic is working

### Issue: Empty Responses

**Check Backend Logs**:
- Look for: `⚠️ Answer was empty, using fallback`
- Look for: `✅ Mock LLM generated answer...` or `✅ GPT-4 generated answer...`

**Fix**:
- Ensure fallback function is working
- Check if LLM is generating responses
- Verify error handling is catching issues

### Issue: Backend Crashes on Startup

**Check**:
- Python version (should be 3.9+)
- All dependencies installed
- FAISS index exists

**Fix**:
```bash
cd backend
pip install -r requirements.txt
python -m rag.ingest  # If index missing
```

## Expected Backend Logs for Successful Request

When you send "I need health insurance for 57 year old male":

```
🔍 Query analysis: health=True, car=False, bike=False, intent=True, insurance=True, policy=False, is_insurance_query=True
📋 No context but specific insurance query detected: 'I need health insurance for 57 year old male', SKIPPING LLM and using detailed fallback
✅ Retriever returned zero chunks after filtering
```

OR if FAISS index exists:

```
🔍 Query analysis: health=True, car=False, bike=False, intent=True, insurance=True, policy=False, is_insurance_query=True
✅ Retriever initialized successfully
✅ GPT-4 generated answer: XXX chars
```

## Quick Test Script

Create `test_backend.sh`:
```bash
#!/bin/bash
echo "Testing Health Endpoint..."
curl http://localhost:8000/health

echo -e "\n\nTesting Chat Endpoint..."
curl -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need health insurance for 57 year old male"}' | python -m json.tool
```

Run: `chmod +x test_backend.sh && ./test_backend.sh`

## Success Criteria

✅ Backend starts without errors
✅ Health endpoint returns `{"status":"ok"}`
✅ Chat endpoint returns valid JSON
✅ Answers are specific and detailed (not generic)
✅ Follow-up questions are asked
✅ Session ID is returned
✅ Frontend displays responses correctly
✅ No "Failed to fetch" errors
✅ No generic "I'm here to help" messages

If all these pass, the chatbot is working correctly!

