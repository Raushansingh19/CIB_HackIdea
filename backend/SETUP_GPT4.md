# Setting Up GPT-4 for Anti-Hallucination

This guide explains how to configure the chatbot to use GPT-4 with strict anti-hallucination controls.

## Quick Setup

1. **Install OpenAI package:**
   ```bash
   cd backend
   pip install openai
   ```

2. **Get your OpenAI API key:**
   - Sign up at https://platform.openai.com/
   - Go to API Keys section
   - Create a new secret key
   - Copy the key (starts with `sk-...`)

3. **Set the API key as environment variable:**
   
   **Linux/Mac:**
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"
   ```
   
   **Windows:**
   ```cmd
   set OPENAI_API_KEY=sk-your-key-here
   ```
   
   **Or create a `.env` file in the `backend/` directory:**
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

4. **Update config (optional):**
   The default is already set to use GPT-4. You can verify in `backend/config.py`:
   ```python
   LLM_MODEL_NAME: str = "gpt-4"
   LLM_TEMPERATURE: float = 0.0  # Low temperature prevents hallucination
   ```

5. **Restart the backend server:**
   ```bash
   python main.py
   ```

## Anti-Hallucination Features

The system is configured with multiple layers to prevent hallucination:

### 1. **Strict System Prompt**
- Explicitly instructs GPT-4 to use ONLY provided context
- Forbids using training data knowledge
- Requires saying "I don't know" if information is missing

### 2. **Temperature = 0.0**
- Makes responses deterministic and factual
- Reduces creative/inventive responses
- Focuses on exact information from context

### 3. **Context-Only Responses**
- All answers must be based on retrieved policy chunks
- No external knowledge is used
- Sources are always cited

### 4. **Explicit "I Don't Know" Responses**
- If information isn't in context, GPT-4 is instructed to say so
- Prevents making up information
- Directs users to contact customer service

## Model Options

You can use different GPT models by setting `LLM_MODEL_NAME`:

- `"gpt-4"` - Standard GPT-4 (recommended)
- `"gpt-4-turbo-preview"` - Latest GPT-4 Turbo
- `"gpt-3.5-turbo"` - Faster and cheaper, but less capable
- `"mock-llm"` - Fallback mock (no API needed)

## Cost Considerations

- GPT-4 is more expensive than GPT-3.5
- Each query uses tokens (input + output)
- Monitor usage at https://platform.openai.com/usage

## Testing

After setup, test with:

```bash
curl -X POST http://localhost:8000/api/chat-text \
  -H "Content-Type: application/json" \
  -d '{"message": "What is covered under health insurance?"}'
```

You should see in the backend logs:
```
Using gpt-4 with anti-hallucination controls
```

## Troubleshooting

### "OpenAI package not installed"
```bash
pip install openai
```

### "OPENAI_API_KEY not set"
- Set the environment variable (see step 3 above)
- Or create a `.env` file in `backend/` directory

### "Error calling GPT-4 API"
- Check your API key is valid
- Verify you have credits in your OpenAI account
- Check your internet connection

### Still using Mock LLM?
- Check backend logs for warnings
- Verify `LLM_MODEL_NAME` is not "mock-llm"
- Ensure `OPENAI_API_KEY` is set correctly

## Verification

The system will automatically:
1. Try to use GPT-4 if API key is set
2. Fall back to Mock LLM if OpenAI is unavailable
3. Log which LLM is being used in the console

Check the backend terminal output to see which LLM is active.

