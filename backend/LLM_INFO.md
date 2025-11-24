# LLM Information

## Current Implementation: Mock LLM

The chatbot currently uses a **Mock LLM** for local development. This is a rule-based system that:

1. **Extracts information** from retrieved policy document chunks
2. **Formats responses** based on the user's query type (coverage, exclusions, limits, EMI, etc.)
3. **Cites sources** by referencing policy IDs and clause types
4. **Works entirely offline** - no API keys or external services required

### How the Mock LLM Works

- **Query Analysis**: Detects what the user is asking about (coverage, exclusions, limits, premium/EMI)
- **Context Extraction**: Uses the top 3 most relevant chunks from the RAG retrieval
- **Response Generation**: Formats a coherent answer based on the retrieved policy information
- **Source Citation**: Includes policy IDs and references

### Why Mock LLM?

- **No API costs**: Works completely offline
- **Fast responses**: No network latency
- **Privacy**: All processing happens locally
- **Demo-ready**: Perfect for development and testing

### Limitations

- **Not a real LLM**: Responses are based on direct text extraction, not true language understanding
- **Limited reasoning**: Cannot handle complex multi-step queries
- **No conversation memory**: Each query is independent

## Upgrading to a Real LLM

To use a real LLM (OpenAI, Anthropic, etc.):

1. **Update `backend/config.py`**:
   ```python
   LLM_MODEL_NAME = "gpt-3.5-turbo"  # or "gpt-4", "claude-3", etc.
   OPENAI_API_KEY = "your-api-key-here"
   ```

2. **Modify `backend/rag/llm_chain.py`**:
   - Replace the `MockLLM` class with actual LLM calls
   - Uncomment and implement the LangChain integration
   - Example:
     ```python
     from langchain.llms import OpenAI
     llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
     answer = llm(prompt)
     ```

3. **Install required packages**:
   ```bash
   pip install openai langchain
   ```

## Recommended LLM Providers

- **OpenAI GPT-3.5/GPT-4**: Best for general use, good RAG support
- **Anthropic Claude**: Excellent for long contexts, good reasoning
- **Local LLMs** (Ollama, LlamaCPP): Free, private, but requires more setup
- **Google Gemini**: Good alternative to OpenAI

## Current Status

✅ **Mock LLM is working** - The system uses a rule-based approach that extracts and formats information from policy documents. This works well for straightforward questions about coverage, exclusions, and limits.

For production use with complex queries, consider upgrading to a real LLM.

