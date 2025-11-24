# Troubleshooting Guide

## Common Errors and Solutions

### Error: "Sorry, I encountered an error. Please try again."

This error can occur for several reasons. Here's how to diagnose and fix:

#### 1. Vector Index Not Found

**Symptoms**: Error when trying to retrieve information

**Solution**:
```bash
cd backend
python -m rag.ingest
```

This will build the FAISS vector index from policy documents.

#### 2. Import Errors

**Symptoms**: ModuleNotFoundError or ImportError

**Solution**:
- Make sure you're in the `backend` directory when running commands
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using the correct Python environment (virtual environment)

#### 3. Retrieval Fails

**Symptoms**: Empty results or retrieval errors

**Possible causes**:
- Vector index is corrupted → Rebuild: `python -m rag.ingest`
- Embedding model not loaded → Check that sentence-transformers is installed
- No matching chunks → Try rephrasing your question

#### 4. LLM Generation Errors

**Current Status**: The system uses a **Mock LLM** (not a real LLM)

**What is Mock LLM?**
- A rule-based system that extracts information from policy documents
- Works offline, no API keys needed
- Formats responses based on query type (coverage, exclusions, limits, etc.)

**If you want a real LLM**:
1. See `backend/LLM_INFO.md` for upgrade instructions
2. Add your API key to `backend/config.py`
3. Update `backend/rag/llm_chain.py` to use real LLM

#### 5. Port Already in Use

**Symptoms**: Server won't start, port 8000 in use

**Solution**:
```bash
# Change port in backend/config.py or use:
uvicorn main:app --port 8001
```

#### 6. CORS Errors (Frontend can't connect)

**Symptoms**: Frontend shows network errors

**Solution**:
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Verify frontend is trying to connect to `http://localhost:8000`

## Verification Steps

1. **Check if vector index exists**:
   ```bash
   ls -la backend/data/vector_store/
   ```
   Should show `policy_index.index` and `policy_index_metadata.pkl`

2. **Test backend health**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"ok"}`

3. **Test text chat endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/chat-text \
     -H "Content-Type: application/json" \
     -d '{"message": "What is covered under health insurance?"}'
   ```

4. **Check backend logs**:
   Look for error messages in the terminal where the backend is running

## Current LLM Status

**LLM Type**: Mock LLM (Rule-based, offline)

**Capabilities**:
- ✅ Answers questions about policy coverage
- ✅ Identifies exclusions and limits
- ✅ Cites policy sources
- ✅ Suggests relevant policies
- ❌ Cannot handle complex multi-step reasoning
- ❌ No conversation memory

**To Upgrade to Real LLM**: See `backend/LLM_INFO.md`

## Getting Help

If errors persist:
1. Check backend terminal for detailed error messages
2. Verify all setup steps in README.md were completed
3. Ensure vector index was built successfully
4. Check that all dependencies are installed

