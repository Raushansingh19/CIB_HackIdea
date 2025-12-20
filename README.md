# Insurance Chatbot - CIB HackIdea

An end-to-end insurance chatbot application with RAG (Retrieval-Augmented Generation) that supports both text and audio interactions. The chatbot can answer questions about insurance policies (health, car, bike) and suggest relevant policies based on user queries.

## 🎯 Features

- **Text Chat**: Ask questions via text input
- **Audio Chat**: Record audio questions and receive audio responses with real-time transcription
- **RAG Pipeline**: Uses FAISS vector store and semantic search for accurate answers
- **GPT-4 Integration**: Uses GPT-4 with strict anti-hallucination controls
- **OpenAI Whisper STT**: Real-time speech-to-text transcription (auto-enabled with API key)
- **Policy Suggestions**: Automatically suggests relevant insurance policies with website links
- **Source Citations**: Shows which policy documents were used to generate answers
- **Conversation Memory**: Maintains context across multiple messages in a session
- **Anti-Hallucination**: Configured to prevent making up information, only uses provided context

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Chat UI    │  │ AudioRecorder│  │  Message     │         │
│  │              │  │              │  │  Display     │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                           │                                    │
│                    HTTP/REST API                                │
└───────────────────────────┼────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                          │  │
│  │  • GET  /health                                           │  │
│  │  • POST /api/chat-text                                    │  │
│  │  • POST /api/chat-audio                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│         ┌───────────────────┴───────────────────┐              │
│         │                                       │              │
│         ▼                                       ▼              │
│  ┌──────────────┐                      ┌──────────────┐       │
│  │ STT Service  │                      │ TTS Service  │       │
│  │ (Whisper/   │                      │ (Mock/Polly) │       │
│  │  Mock)      │                      │              │       │
│  └──────────────┘                      └──────────────┘       │
│         │                                       │              │
│         └───────────────────┬───────────────────┘              │
│                             │                                  │
│                             ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              RAG Pipeline                                │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │  │
│  │  │  Retrieval  │→ │  LLM Chain    │→ │  Policy       │ │  │
│  │  │  (FAISS)    │  │  (GPT-4)     │  │  Suggester    │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Conversation Memory (In-Memory Sessions)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Policy      │  │  FAISS       │  │  Embeddings  │         │
│  │  Documents   │  │  Vector      │  │  (Sentence  │         │
│  │  (JSON)      │  │  Index       │  │  Transformers)│       │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### Backend Components

1. **FastAPI Application (`main.py`)**
   - RESTful API endpoints
   - Request/response handling
   - Error handling and validation
   - CORS middleware
   - Static file serving for audio

2. **RAG Pipeline**
   - **Ingestion (`rag/ingest.py`)**: Loads, chunks, and indexes policy documents
   - **Retrieval (`rag/retrieval.py`)**: Semantic search using FAISS
   - **LLM Chain (`rag/llm_chain.py`)**: GPT-4 integration with RAG context

3. **Services**
   - **STT Service (`services/stt_service.py`)**: Speech-to-text (Whisper/Mock)
   - **TTS Service (`services/tts_service.py`)**: Text-to-speech (Mock/Polly)
   - **Policy Suggester (`services/policy_suggester.py`)**: Suggests relevant policies
   - **Conversation Memory (`services/conversation_memory.py`)**: Session management

4. **Data Models (`models/schemas.py`)**
   - Pydantic models for request/response validation
   - Type-safe data structures

#### Frontend Components

1. **Chat Component (`components/Chat.jsx`)**
   - Main chat interface
   - Message history display
   - Text input handling
   - Policy suggestions display
   - Source citations

2. **Audio Recorder (`components/AudioRecorder.jsx`)**
   - Browser MediaRecorder API integration
   - Audio recording and playback
   - Upload to backend

---

## 🔄 System Flow

### Text Chat Flow

```
User Types Message
       │
       ▼
┌─────────────────┐
│  Frontend       │
│  (Chat.jsx)     │
└────────┬────────┘
         │ POST /api/chat-text
         │ {message, session_id}
         ▼
┌─────────────────────────────────┐
│  Backend (main.py)              │
│  1. Get/Create Session          │
│  2. Get Conversation History    │
│  3. Add User Message to History │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Retrieval (retrieval.py)       │
│  1. Embed User Query            │
│  2. FAISS Similarity Search     │
│  3. Filter by Metadata          │
│  4. Return Top-K Chunks         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  LLM Chain (llm_chain.py)       │
│  1. Format Context from Chunks  │
│  2. Build System + User Prompt  │
│  3. Call GPT-4 API              │
│  4. Parse Response               │
│  5. Fallback if Empty/Error     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Policy Suggester               │
│  1. Score Policies by Relevance │
│  2. Return Top 3 Suggestions    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Format Response                │
│  • Answer Text                  │
│  • Policy Suggestions           │
│  • Source Citations             │
│  • Session ID                   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Add Assistant Response         │
│  to Conversation History        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Return JSON Response           │
│  to Frontend                    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Frontend Displays              │
│  • Bot Response                 │
│  • Policy Suggestions           │
│  • Source Citations             │
└─────────────────────────────────┘
```

### Audio Chat Flow

```
User Clicks Record
       │
       ▼
┌─────────────────────────────────┐
│  Frontend (AudioRecorder.jsx)   │
│  1. Request Microphone Access    │
│  2. Start MediaRecorder          │
│  3. Collect Audio Chunks         │
└────────┬────────────────────────┘
         │
         │ User Stops Recording
         ▼
┌─────────────────────────────────┐
│  Create Audio Blob              │
│  Send to /api/chat-audio        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Backend (main.py)              │
│  1. Save Uploaded Audio File    │
│  2. Check File Size              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  STT Service (stt_service.py)   │
│  Auto-detect:                    │
│  • If OPENAI_API_KEY → Whisper  │
│  • Else → Mock STT              │
│  Returns: Transcript            │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Same as Text Chat Flow:        │
│  • Retrieval                    │
│  • LLM Chain                    │
│  • Policy Suggestions           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  TTS Service (tts_service.py)   │
│  Generate Audio from Answer     │
│  Save to data/audio_output/     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Return Response with:          │
│  • Transcript                    │
│  • Answer                       │
│  • Audio URL                    │
│  • Suggestions                  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Frontend:                      │
│  1. Display Transcript          │
│  2. Display Bot Response        │
│  3. Play TTS Audio              │
└─────────────────────────────────┘
```

### RAG Pipeline Flow (Detailed)

```
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION PHASE                          │
│                    (One-time setup)                         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Load Policy Documents (JSON)                            │
│     • health_policy_1.json                                 │
│     • car_policy_1.json                                     │
│     • bike_policy_1.json                                    │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Chunk Text                                              │
│     • Split into 500-char chunks                            │
│     • 50-char overlap                                       │
│     • Preserve metadata (policy_id, type, region)           │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Generate Embeddings                                      │
│     • Use Sentence Transformers (all-MiniLM-L6-v2)          │
│     • Convert chunks to 384-dim vectors                     │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Build FAISS Index                                       │
│     • Store vectors in FAISS index                          │
│     • Save metadata separately (pickle)                     │
│     • Save to data/vector_store/                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    RETRIEVAL PHASE                          │
│                    (Per Query)                              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Load FAISS Index & Metadata                             │
│     • Load from data/vector_store/                          │
│     • Initialize embedding model                            │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Embed User Query                                         │
│     • Same embedding model as documents                     │
│     • Convert query to 384-dim vector                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Similarity Search                                        │
│     • FAISS computes cosine similarity                      │
│     • Retrieve top-k candidates (k * 2 if filters)         │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Filter by Metadata                                      │
│     • Filter by policy_type (if specified)                  │
│     • Filter by region (if specified)                        │
│     • Return top-k after filtering                          │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Return Retrieved Chunks                                 │
│     • List of RetrievedChunk objects                        │
│     • Each with: text, policy_id, metadata                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    GENERATION PHASE                          │
│                    (Per Query)                              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Check if Chunks Available                                │
│     • If chunks → Use context mode                          │
│     • If no chunks → Use general mode                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Build Prompt                                            │
│     • System Prompt (context-aware or general)              │
│     • Format retrieved chunks as context                    │
│     • Include conversation history                          │
│     • Add user query                                         │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Call GPT-4 API                                          │
│     • Send messages array                                   │
│     • Temperature = 0.0 (deterministic)                     │
│     • Max tokens = 1200                                      │
│     • Retry logic (2 retries)                               │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Parse & Validate Response                               │
│     • Extract answer text                                   │
│     • Check for empty/error responses                       │
│     • Fallback if needed                                    │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Return Answer + Metadata                                │
│     • Answer text                                           │
│     • Supporting info (mode, small_talk flag)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings (Pydantic)
│   ├── requirements.txt        # Python dependencies
│   ├── models/
│   │   └── schemas.py          # Pydantic data models (request/response)
│   ├── rag/
│   │   ├── ingest.py           # Policy document ingestion & indexing
│   │   ├── retrieval.py        # Semantic search retrieval (FAISS)
│   │   └── llm_chain.py        # LLM + RAG chain (GPT-4 integration)
│   ├── services/
│   │   ├── stt_service.py      # Speech-to-Text service (Whisper/Mock)
│   │   ├── tts_service.py      # Text-to-Speech service (Mock/Polly)
│   │   ├── policy_suggester.py # Policy suggestion logic
│   │   └── conversation_memory.py # Session & conversation history
│   └── data/
│       ├── policies/           # Policy JSON files (input)
│       ├── vector_store/       # FAISS index (generated by ingest)
│       ├── audio_output/       # TTS audio files (generated)
│       └── temp_uploads/       # Temporary audio uploads (STT)
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx              # Main React app
        ├── main.jsx             # React entry point
        └── components/
            ├── Chat.jsx         # Main chat UI component
            ├── Chat.css         # Chat styling
            ├── AudioRecorder.jsx # Audio recording component
            └── AudioRecorder.css # Audio recorder styling
```

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- OpenAI API key (for GPT-4 and Whisper - optional but recommended)

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

4. **Set up GPT-4 and Whisper (Recommended):**
   
   Get your OpenAI API key from https://platform.openai.com/
   
   **Set environment variable:**
   ```bash
   export OPENAI_API_KEY="sk-your-key-here"  # Linux/Mac
   # OR
   set OPENAI_API_KEY=sk-your-key-here  # Windows
   ```
   
   **Or create `.env` file in `backend/` directory:**
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```
   
   See `backend/SETUP_GPT4.md` for detailed instructions.

5. **Run the ingestion pipeline to build the vector index:**
   ```bash
   python -m rag.ingest
   ```
   
   This will:
   - Load policy documents from `data/policies/`
   - Chunk and embed the documents
   - Build a FAISS vector index
   - Save the index to `data/vector_store/`

6. **Start the FastAPI server:**
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
   
   The frontend will be available at `http://localhost:3000` (or the port shown)

---

## 💬 Usage

### Text Chat

1. Type your question in the text input field
2. Click "Send" or press Enter
3. View the bot's response with:
   - Answer text
   - Suggested policies (with website links)
   - Source citations (click "View Sources" to expand)

### Audio Chat

1. Click the "Record Audio" button
2. Speak your question (microphone permission required)
3. Click "Stop Recording" when done
4. The bot will:
   - Transcribe your audio (using Whisper if API key is set)
   - Process the question through RAG pipeline
   - Return a text answer
   - Generate and play audio response (mock TTS for now)

### Example Questions

- "What is covered under my health insurance policy?"
- "What are the exclusions in car insurance?"
- "What is the maximum coverage limit for bike insurance?"
- "Does my health policy cover pre-existing conditions?"
- "What is the deductible for car insurance?"
- "I need health insurance for a 57 year old male"
- "Compare health and car insurance"

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required for GPT-4 LLM and Whisper STT
OPENAI_API_KEY=your-key-here

# Optional: STT/TTS providers
STT_PROVIDER=auto  # Options: auto, mock, openai-whisper
TTS_PROVIDER=mock  # Options: mock, amazon-polly, google-tts
```

**Note**: 
- `STT_PROVIDER=auto` automatically uses Whisper if `OPENAI_API_KEY` is set
- If `OPENAI_API_KEY` is not set, the system falls back to Mock LLM and Mock STT
- See `backend/SETUP_GPT4.md` for detailed setup instructions

### Backend Configuration

Edit `backend/config.py` to adjust:
- Chunk size and overlap for document chunking
- Number of retrieved chunks (k)
- Embedding model
- STT/TTS providers
- LLM model and temperature

---

## 🔌 API Endpoints

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
  "session_id": "optional-session-id",
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
      "reason": "Highly relevant based on 3 matching clauses",
      "website_url": "https://example.com/health-policy-1"
    }
  ],
  "sources": [
    {
      "policy_id": "health_policy_1",
      "policy_type": "health",
      "clause_type": "coverage",
      "text_snippet": "Health insurance covers..."
    }
  ],
  "session_id": "generated-session-id"
}
```

### `POST /api/chat-audio`
Audio-based chat endpoint.

**Request:**
- `multipart/form-data` with `audio_file` field
- Optional: `session_id` form field

**Response:**
```json
{
  "transcript": "What is covered under health insurance?",
  "answer": "...",
  "policy_suggestions": [...],
  "sources": [...],
  "audio_url": "/audio/response.wav",
  "session_id": "generated-session-id"
}
```

---

## 🛠️ Adding Real STT/TTS Providers

### Speech-to-Text (STT)

The code includes implementations for:
- ✅ **OpenAI Whisper** (auto-enabled with API key)
- ⚠️ Google Cloud Speech-to-Text (placeholder)

**Whisper is automatically used if `OPENAI_API_KEY` is set!**

To use Google Speech:
1. Uncomment the function in `services/stt_service.py`
2. Install: `pip install google-cloud-speech`
3. Set `STT_PROVIDER="google-speech"` in config
4. Configure Google Cloud credentials

### Text-to-Speech (TTS)

The code includes placeholder functions for:
- Amazon Polly
- Google Cloud Text-to-Speech

To implement:
1. Uncomment the relevant function in `services/tts_service.py`
2. Install the required SDK (e.g., `pip install boto3`)
3. Set the `TTS_PROVIDER` environment variable
4. Configure credentials

---

## 🐛 Troubleshooting

### Backend Issues

1. **FAISS index not found:**
   ```bash
   cd backend
   python -m rag.ingest
   ```

2. **Import errors:**
   - Ensure you're in the backend directory
   - Activate your virtual environment
   - Install all dependencies: `pip install -r requirements.txt`

3. **Port already in use:**
   - Change the port in `config.py` or use: `uvicorn main:app --port 8001`

4. **GPT-4 not working:**
   - Check `OPENAI_API_KEY` is set: `echo $OPENAI_API_KEY`
   - Verify API key is valid
   - Check backend logs for error messages
   - See `backend/SETUP_GPT4.md` for detailed troubleshooting

5. **Whisper transcription not working:**
   - Ensure `OPENAI_API_KEY` is set
   - Check backend logs for transcription errors
   - Verify audio file is being uploaded (check file size in logs)

### Frontend Issues

1. **Cannot connect to backend:**
   - Ensure backend is running on port 8000
   - Check CORS settings in `backend/main.py`
   - Verify `API_BASE_URL` in frontend components

2. **Microphone not working:**
   - Check browser permissions (Chrome: Settings → Privacy → Microphone)
   - Use HTTPS or localhost (required for getUserMedia)
   - Try a different browser

3. **Audio playback issues:**
   - Check browser console for errors
   - Ensure backend audio files are accessible at `/audio/` endpoint
   - Verify TTS service is generating files

---

## 📊 Data Flow Summary

1. **Ingestion** (One-time): Documents → Chunks → Embeddings → FAISS Index
2. **Query** (Per request): User Input → Embed Query → Search FAISS → Retrieve Chunks
3. **Generation**: Chunks + Query → LLM Prompt → GPT-4 → Answer
4. **Enhancement**: Answer + Chunks → Policy Suggestions + Sources
5. **Response**: Answer + Suggestions + Sources → Frontend Display

---

## 🔐 Security Notes

- API keys should never be committed to version control
- Use environment variables or `.env` files (add `.env` to `.gitignore`)
- CORS is configured for local development only
- For production, implement proper authentication and rate limiting

---

## 📝 Development Notes

- The mock STT service returns a generic transcript for demo purposes
- The mock TTS service creates a placeholder WAV file (silence)
- For production, replace mocks with real API integrations
- All code includes detailed comments explaining functionality
- Conversation memory is stored in-memory (not persistent across server restarts)

---

## 🎓 Key Technologies

- **Backend**: FastAPI, Python 3.9+
- **RAG**: FAISS, Sentence Transformers
- **LLM**: OpenAI GPT-4
- **STT**: OpenAI Whisper (auto-enabled)
- **Frontend**: React, Vite
- **Audio**: Browser MediaRecorder API

---

## 📚 Additional Documentation

- `backend/SETUP_GPT4.md` - Detailed GPT-4 setup guide
- `backend/LLM_INFO.md` - LLM configuration information
- `AUDIO_FIX_SUMMARY.md` - Audio transcription fixes
- `TESTING_GUIDE.md` - Testing instructions

---

## 📄 License

This project is provided as-is for educational and development purposes.

---

## 🤝 Contributing

Feel free to extend this project with:
- Additional policy types
- More sophisticated policy suggestion algorithms
- Real TTS provider integrations
- Persistent conversation storage (database)
- User authentication
- Database integration for policies
- Multi-language support

---

## 🎉 Quick Start Summary

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-your-key"  # Optional but recommended
python -m rag.ingest  # Build vector index
python main.py  # Start server

# Frontend (in new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and start chatting! 🚀
