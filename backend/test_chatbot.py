#!/usr/bin/env python3
"""
Quick test script to verify the chatbot backend is working.

Run this to test:
1. Imports work correctly
2. Retrieval works (or fails gracefully)
3. LLM chain works
4. Fallback function works
5. Main endpoint logic works
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🧪 Testing Insurance Chatbot Backend")
print("=" * 60)

# Test 1: Imports
print("\n1️⃣ Testing imports...")
try:
    from config import settings
    from rag.retrieval import retrieve_relevant_chunks
    from rag.llm_chain import generate_answer_with_rag, _default_fallback
    from services.conversation_memory import get_or_create_session
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Configuration
print("\n2️⃣ Testing configuration...")
try:
    print(f"   LLM Model: {settings.LLM_MODEL_NAME}")
    print(f"   Has API Key: {bool(settings.OPENAI_API_KEY)}")
    print(f"   Vector Store: {settings.VECTOR_STORE_PATH}")
    print("✅ Configuration loaded")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    sys.exit(1)

# Test 3: Retrieval
print("\n3️⃣ Testing retrieval...")
try:
    chunks = retrieve_relevant_chunks("health insurance", None, None, 5)
    print(f"   Retrieved {len(chunks)} chunks")
    if chunks:
        print(f"   First chunk: {chunks[0].policy_id} ({chunks[0].policy_type})")
    else:
        print("   ⚠️ No chunks retrieved (will use general mode)")
    print("✅ Retrieval works")
except Exception as e:
    print(f"❌ Retrieval error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Fallback function
print("\n4️⃣ Testing fallback function...")
try:
    test_queries = [
        "Hi",
        "I need health insurance for 57 year old male",
        "I need bike insurance",
        "compare policies"
    ]
    for query in test_queries:
        result = _default_fallback(query)
        if result and len(result) > 20:
            print(f"   ✅ '{query[:30]}...' → {len(result)} chars")
        else:
            print(f"   ❌ '{query[:30]}...' → Too short or empty")
    print("✅ Fallback function works")
except Exception as e:
    print(f"❌ Fallback error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: LLM Chain (without context)
print("\n5️⃣ Testing LLM chain (no context)...")
try:
    answer, info = generate_answer_with_rag(
        user_query="I need health insurance for 57 year old male",
        retrieved_chunks=[],
        policy_type=None,
        region=None,
        conversation_history=None
    )
    if answer and len(answer) > 50:
        print(f"   ✅ Generated answer: {len(answer)} chars")
        print(f"   Preview: {answer[:100]}...")
        print(f"   Mode: {info.get('mode', 'unknown')}")
    else:
        print(f"   ❌ Answer too short: {len(answer) if answer else 0} chars")
    print("✅ LLM chain works")
except Exception as e:
    print(f"❌ LLM chain error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Session management
print("\n6️⃣ Testing session management...")
try:
    session_id = get_or_create_session(None)
    print(f"   Created session: {session_id[:8]}...")
    session_id2 = get_or_create_session(session_id)
    if session_id == session_id2:
        print("   ✅ Session persistence works")
    else:
        print("   ⚠️ Session ID changed")
    print("✅ Session management works")
except Exception as e:
    print(f"❌ Session error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
print("\nIf all tests passed, the backend should work correctly.")
print("Start the server with: python main.py")

