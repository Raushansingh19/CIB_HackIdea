# Complete Fix and Test Guide

## 🔧 What Was Fixed

1. **Initialized `llm_answer` variable** at the start of `generate_answer_with_rag` to prevent undefined variable errors
2. **Fixed code structure** - all functions properly defined
3. **Enhanced error handling** - multiple fallback layers
4. **Improved query detection** - better insurance query recognition
5. **Added test script** - `backend/test_chatbot.py` to verify everything works

## 🚀 How to Test (Step by Step)

### Step 1: Test Backend Components

```bash
cd backend
python test_chatbot.py
```

**Expected Output**:
```
🧪 Testing Insurance Chatbot Backend
============================================================
1️⃣ Testing imports...
✅ All imports successful
2️⃣ Testing configuration...
✅ Configuration loaded
3️⃣ Testing retrieval...
✅ Retrieval works
4️⃣ Testing fallback function...
✅ Fallback function works
5️⃣ Testing LLM chain...
✅ LLM chain works
6️⃣ Testing session management...
✅ Session management works
============================================================
✅ All tests completed!
```

**If any test fails**, that's the issue - fix it first.

### Step 2: Start Backend

```bash
cd backend
python main.py
```

**Look for**:
- No import errors
- No syntax errors
- Server starts on port 8000
- Message: "Uvicorn running on http://0.0.0.0:8000"

**If errors occur**, check:
- Python version (3.9+)
- All dependencies installed: `pip install -r requirements.txt`
- FAISS index exists: `ls data/vector_store/`

### Step 3: Test Backend API Directly

**In a new terminal**, test health:
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"ok"}`

**Test chat endpoint**:
```bash
curl -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need health insurance for 57 year old male"}' \
  | python -m json.tool
```

**Expected**: JSON with `answer` field containing detailed health insurance advice (NOT generic message).

### Step 4: Check Backend Logs

When you send a request, backend should log:
```
🔍 Query analysis: health=True, car=False, bike=True, ...
📋 No context but specific insurance query detected: 'I need health insurance...', SKIPPING LLM and using detailed fallback
```

OR if FAISS index exists:
```
✅ Retriever initialized successfully
✅ GPT-4 generated answer: XXX chars
```

### Step 5: Start Frontend

```bash
cd frontend
npm run dev
```

**Check**:
- Frontend starts on port 5173 (or 3000)
- No build errors
- Browser opens successfully

### Step 6: Test in Browser

1. Open `http://localhost:5173`
2. Open DevTools (F12) → Console tab
3. Try: "I need health insurance for 57 year old male"

**Expected**:
- Backend logs show query analysis
- Response is detailed health insurance advice
- NOT: "I'm here to help" or generic message

## 🐛 Common Issues and Fixes

### Issue 1: "Failed to fetch" in Browser

**Cause**: Backend not running or not accessible

**Fix**:
1. Check backend is running: `ps aux | grep python`
2. Check port: `lsof -i :8000`
3. Test directly: `curl http://localhost:8000/health`
4. Check CORS: Frontend port must be in `backend/config.py` CORS_ORIGINS

### Issue 2: Generic "I'm here to help" Messages

**Cause**: Fallback not being called or query not detected

**Fix**:
1. Check backend logs for: `🔍 Query analysis: ...`
2. Verify `is_insurance_query=True` in logs
3. Check if `_default_fallback` is being called
4. Verify query contains insurance keywords

### Issue 3: Backend Crashes on Request

**Cause**: Missing dependencies or FAISS index

**Fix**:
1. Run test script: `python test_chatbot.py`
2. Install dependencies: `pip install -r requirements.txt`
3. Create FAISS index: `python -m rag.ingest`
4. Check Python version: `python --version` (should be 3.9+)

### Issue 4: Empty Responses

**Cause**: LLM not generating or fallback not working

**Fix**:
1. Check backend logs for LLM errors
2. Verify `_default_fallback` function works: `python -c "from rag.llm_chain import _default_fallback; print(_default_fallback('health insurance'))"`
3. Check if GPT-4 API key is set (if using GPT-4)
4. Verify MockLLM is working if GPT-4 unavailable

## ✅ Success Checklist

- [ ] `python test_chatbot.py` passes all tests
- [ ] Backend starts without errors
- [ ] `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] Chat endpoint returns valid JSON with detailed answer
- [ ] Frontend connects to backend
- [ ] Test queries return specific insurance advice
- [ ] No generic "I'm here to help" messages
- [ ] Follow-up questions are asked
- [ ] Session ID is maintained

## 🎯 Quick Verification

Run this one-liner to test everything:

```bash
cd backend && python test_chatbot.py && echo "✅ Backend ready!" && echo "Now start server: python main.py"
```

Then in another terminal:
```bash
curl -X POST http://localhost:8000/api/chat-text -H "Content-Type: application/json" -d '{"message": "I need health insurance"}' | grep -o '"answer":"[^"]*"' | head -c 200
```

Should show detailed health insurance advice, not generic message.

## 📝 What to Share if Still Not Working

1. Output of `python test_chatbot.py`
2. Backend startup logs
3. Backend logs when sending a test query
4. Browser console errors (F12 → Console)
5. Result of `curl http://localhost:8000/health`
6. Result of chat endpoint curl command

This will help identify the exact issue!

