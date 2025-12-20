# Quick Start Guide - Insurance Chatbot

## ✅ Backend is Working!

Your backend started successfully! The server is running correctly.

## 🚀 How to Use

### Step 1: Start Backend (Keep it Running!)

```bash
cd backend
python main.py
```

**IMPORTANT**: Keep this terminal open and running. Don't press Ctrl+C until you're done testing.

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Step 2: Test Backend (In a NEW Terminal)

Open a **NEW terminal window** (keep backend running in the first one):

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need health insurance for 57 year old male"}'
```

### Step 3: Start Frontend (In Another Terminal)

Open **another terminal window**:

```bash
cd frontend
npm run dev
```

### Step 4: Test in Browser

1. Open browser to `http://localhost:5173` (or the port shown)
2. Open DevTools (F12) → Console tab
3. Try these queries:
   - "Hi"
   - "I need health insurance for 57 year old male"
   - "I need bike insurance"

## 📊 What to Expect

### Backend Logs (when you send a request):

```
🔍 Query analysis: health=True, car=False, bike=False, intent=True, insurance=True, policy=False, is_insurance_query=True
📋 No context but specific insurance query detected: 'I need health insurance for 57 year old male', SKIPPING LLM and using detailed fallback
```

### Frontend Response:

Should show detailed insurance advice, NOT:
- ❌ "I'm here to help you with insurance questions"
- ❌ "It seems the connection was interrupted"
- ✅ Detailed health insurance guidance with bullet points and follow-up questions

## ⚠️ Common Mistakes

1. **Stopping the backend** - Keep `python main.py` running!
2. **Testing in same terminal** - Use a new terminal for curl/frontend
3. **Port mismatch** - Frontend should connect to `http://localhost:8000`

## 🎯 Success Indicators

✅ Backend shows "Application startup complete"
✅ Health endpoint returns `{"status":"ok"}`
✅ Chat endpoint returns JSON with detailed `answer` field
✅ Frontend displays specific insurance advice
✅ No generic error messages

## 🐛 If Something Doesn't Work

1. **Check backend is running** - Look for "Uvicorn running" message
2. **Check backend logs** - When you send a request, logs should appear
3. **Check browser console** - F12 → Console tab for errors
4. **Test with curl first** - Verify backend works before testing frontend

Your backend is working correctly! Just keep it running while testing. 🚀

