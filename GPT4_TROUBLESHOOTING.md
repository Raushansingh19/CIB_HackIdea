# GPT-4 Troubleshooting Guide

## Key File to Modify: `backend/rag/llm_chain.py`

This is the **main file** that controls GPT-4 integration and response quality.

## Common Issues and Fixes

### 1. **Getting Generic Error Messages**

**Problem**: "I'm having trouble processing your request right now..."

**Solution**: The error handling has been improved to:
- Show specific error messages
- Retry on transient failures
- Provide helpful fallback responses
- Log detailed error information

**Check**: Look at backend console logs for specific error messages.

### 2. **GPT-4 Not Being Used**

**Symptoms**: Getting basic responses, not intelligent GPT-4 answers

**Check**:
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Or check in backend/.env file
cat backend/.env | grep OPENAI_API_KEY
```

**Fix**: Set your OpenAI API key:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### 3. **API Errors**

**Common Errors**:

- **Rate Limit (429)**: Too many requests
  - **Fix**: Wait a moment and retry, or upgrade your OpenAI plan
  
- **Invalid API Key (401)**: Wrong or expired key
  - **Fix**: Check your API key at https://platform.openai.com/api-keys
  
- **Insufficient Quota**: No credits remaining
  - **Fix**: Add credits at https://platform.openai.com/account/billing
  
- **Timeout**: Request taking too long
  - **Fix**: Increased timeout to 60 seconds, will retry automatically

### 4. **Poor Response Quality**

**Improvements Made**:

1. **Better System Prompt**: Less restrictive, more helpful
2. **Improved Context Formatting**: Cleaner, more structured
3. **Increased max_tokens**: 1500 tokens for detailed responses
4. **Retry Logic**: Automatically retries on failures
5. **Better Error Messages**: Specific, actionable errors

### 5. **Response Too Slow**

**Optimizations**:
- Timeout set to 60 seconds (was 30)
- Automatic retries with backoff
- Progress logging to see what's happening

## How to Get Better Results

### Modify `backend/rag/llm_chain.py`:

1. **Adjust Temperature** (line ~36 in config.py):
   ```python
   LLM_TEMPERATURE: float = 0.3  # Slightly higher for more natural responses
   ```

2. **Adjust Max Tokens** (line ~140 in llm_chain.py):
   ```python
   max_tokens=2000,  # Increase for longer responses
   ```

3. **Modify System Prompt** (line ~37 in llm_chain.py):
   - Make it less restrictive
   - Add specific instructions for your use case
   - Adjust tone and style

4. **Improve Context Formatting** (line ~310 in llm_chain.py):
   - Add more metadata
   - Structure context better
   - Include policy names, not just IDs

## Testing GPT-4 Integration

1. **Check if GPT-4 is being used**:
   ```bash
   # Start backend and look for:
   🚀 Using gpt-4 API
   ✅ GPT-4 response received in X.XX seconds
   ```

2. **Test with a simple query**:
   ```bash
   curl -X POST http://localhost:8000/api/chat-text \
     -H "Content-Type: application/json" \
     -d '{"message": "What is covered under health insurance?"}'
   ```

3. **Check backend logs** for:
   - API call status
   - Response time
   - Any errors

## Debugging Steps

1. **Verify API Key**:
   ```python
   # In Python console
   from backend.config import settings
   print(f"API Key set: {bool(settings.OPENAI_API_KEY)}")
   print(f"Model: {settings.LLM_MODEL_NAME}")
   ```

2. **Test API Key Directly**:
   ```python
   from openai import OpenAI
   client = OpenAI(api_key="your-key-here")
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[{"role": "user", "content": "Hello"}]
   )
   print(response.choices[0].message.content)
   ```

3. **Check Backend Logs**:
   - Look for error messages
   - Check if GPT-4 is being called
   - Verify response is received

## Best Practices

1. **Always check backend console** for detailed error messages
2. **Set API key in environment variable** (not in code)
3. **Monitor OpenAI usage** at https://platform.openai.com/usage
4. **Use retry logic** for transient failures
5. **Provide good context** in the RAG pipeline

## Quick Fixes

### If getting errors:
1. Check API key is set: `echo $OPENAI_API_KEY`
2. Check backend logs for specific error
3. Verify OpenAI account has credits
4. Try increasing timeout if requests are slow

### If getting poor results:
1. Adjust system prompt in `llm_chain.py`
2. Increase max_tokens for longer responses
3. Improve context formatting
4. Adjust temperature (0.0 = factual, 0.7 = creative)

## Summary

**Main file to modify**: `backend/rag/llm_chain.py`

**Key sections**:
- `SYSTEM_PROMPT` (line ~37): Controls how GPT-4 responds
- `user_prompt` formatting (line ~310): How context is presented
- `GPT4LLM.generate()` (line ~110): API call implementation
- Error handling (line ~325): How errors are handled

The system now has:
- ✅ Better error handling with retries
- ✅ Improved prompts for better results
- ✅ Detailed logging for debugging
- ✅ Helpful fallback responses
- ✅ Specific error messages

