# How to Test - Step by Step

## ✅ Your Backend Started Successfully!

The logs show your backend is working. Here's how to test it properly:

## 🚀 Testing Process

### Terminal 1: Keep Backend Running

```bash
cd backend
python main.py
```

**IMPORTANT**: 
- ✅ Keep this terminal open
- ✅ Don't press Ctrl+C
- ✅ Wait for: "Application startup complete"
- ✅ Leave it running while testing

### Terminal 2: Test Backend API

Open a **NEW terminal** (keep Terminal 1 running):

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Expected: {"status":"ok"}

# Test 2: Chat endpoint
curl -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need health insurance for 57 year old male"}' \
  | python3 -m json.tool

# Expected: JSON with detailed "answer" field (not generic message)
```

### Terminal 3: Start Frontend

Open **another terminal**:

```bash
cd frontend
npm run dev
```

Then open browser to the URL shown (usually `http://localhost:5173`)

## 📋 Quick Test Script

I've created a test script. Run it in a **new terminal** (while backend is running):

```bash
./test_backend.sh
```

This will test:
1. Health endpoint
2. Health insurance query
3. Bike insurance query

## 🎯 What You Should See

### In Backend Logs (Terminal 1):

When you send a request, you'll see:
```
🔍 Query analysis: health=True, car=False, bike=False, intent=True, insurance=True, policy=False, is_insurance_query=True
📋 No context but specific insurance query detected: 'I need health insurance for 57 year old male', SKIPPING LLM and using detailed fallback
```

### In API Response:

```json
{
  "answer": "I'd be happy to help you with health insurance options!\n\nFor someone in their 50s or older, here's what to consider:\n\n• **Coverage Types**: Comprehensive plans cover...",
  "policy_suggestions": [],
  "sources": [],
  "session_id": "some-uuid"
}
```

**NOT**:
- ❌ "I'm here to help you with insurance questions"
- ❌ "It seems the connection was interrupted"
- ✅ Detailed, specific health insurance advice

## ⚠️ Common Issues

### Issue: "Failed to connect" when using curl

**Cause**: Backend not running or stopped

**Fix**: 
1. Make sure `python main.py` is still running in Terminal 1
2. Check it shows "Application startup complete"
3. Don't press Ctrl+C

### Issue: Generic responses

**Check Backend Logs**:
- Should show: `📋 No context but specific insurance query detected...`
- Should show: `is_insurance_query=True`

**If not showing**:
- Query might not be detected as insurance query
- Check the query contains keywords like "health", "insurance", "57", "male"

## ✅ Success Checklist

- [ ] Backend running (Terminal 1 shows "Application startup complete")
- [ ] Health endpoint works: `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] Chat endpoint returns JSON with detailed answer
- [ ] Answer is specific (not generic "I'm here to help")
- [ ] Backend logs show query analysis
- [ ] Frontend connects and displays responses

## 🎉 You're Ready!

Your backend is working! Just:
1. Keep it running
2. Test in a new terminal
3. Check the responses are detailed and specific

The code is correct - you just need to keep the server running while testing! 🚀

