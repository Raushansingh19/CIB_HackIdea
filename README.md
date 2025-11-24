<<<<<<< HEAD
# Insurance Chatbot

An end-to-end insurance chatbot application with RAG (Retrieval-Augmented Generation) that supports both text and audio interactions. The chatbot can answer questions about insurance policies (health, car, bike) and suggest relevant policies based on user queries.

## Features

- **Text Chat**: Ask questions via text input
- **Audio Chat**: Record audio questions and receive audio responses
- **RAG Pipeline**: Uses FAISS vector store and semantic search for accurate answers
- **GPT-4 Integration**: Uses GPT-4 with strict anti-hallucination controls
- **Policy Suggestions**: Automatically suggests relevant insurance policies
- **Source Citations**: Shows which policy documents were used to generate answers
- **Anti-Hallucination**: Configured to prevent making up information, only uses provided context

## Architecture

### Backend (Python/FastAPI)
- **Framework**: FastAPI
- **RAG**: LangChain-style pipeline with FAISS vector store
- **Embeddings**: Sentence Transformers (local, no API key needed)
- **LLM**: Mock LLM for local development (easily replaceable with OpenAI/other providers)
- **STT/TTS**: Pluggable services (mock implementations included)

### Frontend (React)
- **Framework**: React with Vite
- **Audio**: Browser MediaRecorder API for recording
- **UI**: Clean chat interface with message bubbles, policy suggestions, and source citations

## Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── requirements.txt        # Python dependencies
│   ├── models/
│   │   └── schemas.py          # Pydantic data models
│   ├── rag/
│   │   ├── ingest.py           # Policy document ingestion
│   │   ├── retrieval.py        # Semantic search retrieval
│   │   └── llm_chain.py        # LLM + RAG chain
│   ├── services/
│   │   ├── stt_service.py      # Speech-to-Text service
│   │   ├── tts_service.py      # Text-to-Speech service
│   │   └── policy_suggester.py # Policy suggestion logic
│   └── data/
│       ├── policies/           # Policy JSON files
│       ├── vector_store/       # FAISS index (generated)
│       ├── audio_output/       # TTS audio files
│       └── temp_uploads/       # Temporary audio uploads
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx
        ├── main.jsx
        └── components/
            ├── Chat.jsx
            └── AudioRecorder.jsx
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up GPT-4 (Required for production):**
   
   Get your OpenAI API key from https://platform.openai.com/
   
   **Set environment variable:**
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"  # Linux/Mac
   # OR
   set OPENAI_API_KEY=sk-your-key-here  # Windows
   ```
   
   **Or create `.env` file in `backend/` directory:**
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
   
   See `backend/SETUP_GPT4.md` for detailed instructions.

4. **Run the ingestion pipeline to build the vector index:**
   ```bash
   python -m rag.ingest
   ```
   
   This will:
   - Load policy documents from `data/policies/`
   - Chunk and embed the documents
   - Build a FAISS vector index
   - Save the index to `data/vector_store/`

5. **Start the FastAPI server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## Usage

### Text Chat

1. Type your question in the text input field
2. Click "Send" or press Enter
3. View the bot's response with:
   - Answer text
   - Suggested policies
   - Source citations (click "View Sources" to expand)

### Audio Chat

1. Click the "Record Audio" button
2. Speak your question (microphone permission required)
3. Click "Stop Recording" when done
4. The bot will:
   - Transcribe your audio
   - Process the question
   - Return a text answer
   - Generate and play audio response

### Example Questions

- "What is covered under my health insurance policy?"
- "What are the exclusions in car insurance?"
- "What is the maximum coverage limit for bike insurance?"
- "Does my health policy cover pre-existing conditions?"
- "What is the deductible for car insurance?"

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required for GPT-4 LLM
OPENAI_API_KEY=your-key-here

# Optional: For real STT/TTS providers
STT_PROVIDER=openai-whisper
TTS_PROVIDER=amazon-polly
TTS_REGION=us-east-1
```

**Note**: The system uses GPT-4 by default. If `OPENAI_API_KEY` is not set, it will fall back to a Mock LLM. See `backend/SETUP_GPT4.md` for setup instructions.

### Backend Configuration

Edit `backend/config.py` to adjust:
- Chunk size and overlap for document chunking
- Number of retrieved chunks (k)
- Embedding model
- STT/TTS providers

## Adding Real STT/TTS Providers

### Speech-to-Text (STT)

The code includes placeholder functions for:
- OpenAI Whisper API
- Google Cloud Speech-to-Text

To implement:
1. Uncomment the relevant function in `services/stt_service.py`
2. Install the required SDK (e.g., `pip install openai`)
3. Set the `STT_PROVIDER` environment variable
4. Add API keys to your `.env` file

### Text-to-Speech (TTS)

The code includes placeholder functions for:
- Amazon Polly
- Google Cloud Text-to-Speech

To implement:
1. Uncomment the relevant function in `services/tts_service.py`
2. Install the required SDK (e.g., `pip install boto3`)
3. Set the `TTS_PROVIDER` environment variable
4. Configure credentials

## Adding Real LLM Integration

To replace the mock LLM with a real provider:

1. **OpenAI (via LangChain):**
   ```python
   from langchain.llms import OpenAI
   from langchain.prompts import PromptTemplate
   
   llm = OpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
   answer = llm(prompt)
   ```

2. **Update `rag/llm_chain.py`:**
   - Replace the `MockLLM` class with actual LLM calls
   - Set `LLM_MODEL_NAME` in config to your model name
   - Add API key to environment variables

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{"status": "ok"}
```

### `POST /api/chat-text`
Text-based chat endpoint.

**Request:**
```json
{
  "message": "What is covered under health insurance?",
  "session_id": null,
  "policy_type": "health",
  "region": "US"
}
```

**Response:**
```json
{
  "answer": "Based on the available policy documents...",
  "policy_suggestions": [
    {
      "policy_id": "health_policy_1",
      "policy_type": "health",
      "title": "Comprehensive Health Insurance Plan",
      "reason": "Highly relevant based on 3 matching clauses"
    }
  ],
  "sources": [...]
}
```

### `POST /api/chat-audio`
Audio-based chat endpoint.

**Request:**
- `multipart/form-data` with `audio_file` field

**Response:**
```json
{
  "transcript": "What is covered under health insurance?",
  "answer": "...",
  "policy_suggestions": [...],
  "sources": [...],
  "audio_url": "/audio/response.wav"
}
```

## Troubleshooting

### Backend Issues

1. **FAISS index not found:**
   - Run `python -m rag.ingest` to build the index

2. **Import errors:**
   - Ensure you're in the backend directory
   - Activate your virtual environment
   - Install all dependencies: `pip install -r requirements.txt`

3. **Port already in use:**
   - Change the port in `config.py` or use: `uvicorn main:app --port 8001`

### Frontend Issues

1. **Cannot connect to backend:**
   - Ensure backend is running on port 8000
   - Check CORS settings in `backend/main.py`

2. **Microphone not working:**
   - Check browser permissions
   - Use HTTPS or localhost (required for getUserMedia)

3. **Audio playback issues:**
   - Check browser console for errors
   - Ensure backend audio files are accessible at `/audio/` endpoint

## Development Notes

- The mock STT service returns a fixed transcript for demo purposes
- The mock TTS service creates a placeholder WAV file (silence)
- For production, replace mocks with real API integrations
- All code includes detailed comments explaining functionality

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to extend this project with:
- Additional policy types
- More sophisticated policy suggestion algorithms
- Real STT/TTS provider integrations
- Session management and conversation history
- User authentication
- Database integration for policies

=======
# CIB_HackIdea
CIB Hackathon repo
>>>>>>> 2097657607b8521e97a2e137be726ad862b4b7ed
