#!/bin/bash

echo "🧪 Testing Insurance Chatbot Backend"
echo "===================================="
echo ""

# Test 1: Health endpoint
echo "1️⃣ Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if [ "$HEALTH_RESPONSE" == '{"status":"ok"}' ]; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed: $HEALTH_RESPONSE"
    echo "   Make sure backend is running: python main.py"
    exit 1
fi

echo ""

# Test 2: Chat endpoint - Health insurance query
echo "2️⃣ Testing chat endpoint (health insurance query)..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need health insurance for 57 year old male"}')

# Check if response contains answer field
if echo "$CHAT_RESPONSE" | grep -q '"answer"'; then
    ANSWER=$(echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', '')[:200])" 2>/dev/null)
    if [ -n "$ANSWER" ] && [ ${#ANSWER} -gt 50 ]; then
        echo "   ✅ Chat endpoint working"
        echo "   Answer preview: ${ANSWER}..."
    else
        echo "   ⚠️ Chat endpoint returned short/empty answer"
        echo "   Full response: $CHAT_RESPONSE"
    fi
else
    echo "   ❌ Chat endpoint failed or returned invalid JSON"
    echo "   Response: $CHAT_RESPONSE"
    exit 1
fi

echo ""

# Test 3: Chat endpoint - Bike insurance query
echo "3️⃣ Testing chat endpoint (bike insurance query)..."
BIKE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need bike insurance"}')

if echo "$BIKE_RESPONSE" | grep -q '"answer"'; then
    ANSWER=$(echo "$BIKE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', '')[:200])" 2>/dev/null)
    if [ -n "$ANSWER" ] && [ ${#ANSWER} -gt 50 ]; then
        echo "   ✅ Bike insurance query working"
        echo "   Answer preview: ${ANSWER}..."
    else
        echo "   ⚠️ Bike query returned short answer"
    fi
else
    echo "   ❌ Bike query failed"
fi

echo ""
echo "===================================="
echo "✅ Backend tests completed!"
echo ""
echo "If all tests passed, your backend is working correctly!"
echo "Now start the frontend and test in browser."

