# Streamlit Agent

A production-ready Streamlit application that acts as an AI agent with access to JSONPlaceholder API tools via an MCP server.

## Features

- **Multi-Provider LLM Support** — OpenAI, Groq, Hugging Face Inference API
- **Streaming Responses** — Real-time token-by-token display with thinking indicator
- **Conversation Memory** — Full chat history with session state persistence
- **Tool Call Management** — Automatic tool calling and result aggregation
- **Configurable Agent** — Customize system prompt, temperature, and model
- **MCP Health Check** — Monitor MCP server connectivity
- **Production-Ready** — Type hints, logging, error handling, clean architecture

## Quick Start

### Prerequisites

- Python 3.9+
- An LLM API key (OpenAI, Groq, or Hugging Face)
- Running MCP server (from parent project)

### Installation

1. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and MCP server URL
   ```

### Running Locally

```bash
# Ensure MCP server is running in another terminal
# python -m app.main

# Start Streamlit agent
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Configuration

### Environment Variables

**Required:**
- `LLM_PROVIDER` — LLM provider (openai, groq, huggingface)
- `LLM_API_KEY` — API key for your LLM provider
- `LLM_MODEL` — Model name (e.g., gpt-4o-mini, mixtral-8x7b-32768)
- `MCP_SERVER_URL` — Base URL of your MCP server

**Optional:**
- `STREAMLIT_SERVER_PORT` — Port for Streamlit (default: 8501)
- `STREAMLIT_SERVER_ADDRESS` — Host address (default: localhost)

### Example .env File

```bash
# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-...
LLM_MODEL=gpt-4o-mini
MCP_SERVER_URL=http://localhost:8000
```

```bash
# Groq
LLM_PROVIDER=groq
LLM_API_KEY=gsk-...
LLM_MODEL=mixtral-8x7b-32768
MCP_SERVER_URL=http://localhost:8000
```

## Sidebar Configuration

The application includes a comprehensive sidebar with:

- **LLM Settings**
  - Provider selection (OpenAI, Groq, Hugging Face)
  - API key status indicator
  - Model selection dropdown
  - Temperature slider (0.0 - 2.0)
  - Max tokens input (256 - 4096)

- **MCP Server**
  - URL configuration
  - Health check button
  - Connection status indicator

- **Agent Settings**
  - System prompt customization
  - Dynamic configuration update

- **Conversation**
  - Clear conversation history button
  - Message count indicator

## Chat Interface

### User Messages
Enter your query in the chat input at the bottom of the screen. Examples:

- "Show me posts by user 5"
- "Get comments for post 1"
- "List all users"
- "What posts did user 3 write?"

### Assistant Responses
The agent will:
1. Stream tokens in real-time with a thinking indicator
2. Call appropriate tools when needed
3. Aggregate tool results
4. Return final response

### Tool Calls
Tool executions are displayed with expandable sections showing:
- Tool name
- Arguments sent to the tool
- Results returned from MCP server

## Architecture

```
app.py                          # Main Streamlit entry point
├── UI Components
│   ├── Sidebar configuration
│   ├── Chat interface
│   └── Message rendering
├── Agent Integration
│   ├── LLM communication
│   ├── Streaming responses
│   └── Error handling
└── agent/
    ├── agent_logic.py         # Agent orchestration
    ├── llm_client.py          # LLM provider abstraction
    └── mcp_client.py          # MCP server communication
```

## API Integration

### Supported LLM Providers

#### OpenAI
```python
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-...
LLM_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo
```

#### Groq (Fast & Free)
```python
LLM_PROVIDER=groq
LLM_API_KEY=gsk-...
LLM_MODEL=llama-3.1-8b-instant  # Groq models change frequently - check console.groq.com for current options
```

#### Hugging Face
```python
LLM_PROVIDER=huggingface
LLM_API_KEY=hf_...
LLM_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
```

### MCP Server Integration

The agent communicates with your MCP server via HTTP:

**Available Tools:**
- `get_post(post_id)` — Fetch a single post
- `list_posts(user_id=None)` — List posts, optionally filtered
- `get_comments_for_post(post_id)` — Get comments on a post
- `get_user(user_id)` — Get user details
- `list_users()` — List all users

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create new app → select repository
4. Set `app.py` as main file
5. Add secrets for `LLM_API_KEY` and `MCP_SERVER_URL`

### Render

1. Create new Web Service
2. Connect GitHub repository
3. **Build command:** `pip install -r streamlit_agent/requirements.txt`
4. **Start command:** `streamlit run streamlit_agent/app.py`
5. Add environment variables in Render dashboard

### Railway

1. Connect GitHub
2. Add environment variables
3. Deploy from `streamlit_agent/` folder

## Troubleshooting

### "API key not found"
- Ensure `.env` file exists in `streamlit_agent/` directory
- Verify `LLM_API_KEY` is set
- Check for typos in environment variable names

### "Cannot connect to MCP server"
- Verify MCP server is running: `python -m app.main`
- Check `MCP_SERVER_URL` is correct (e.g., http://localhost:8000)
- Click "Check MCP Health" button in sidebar

### "Tool call failed"
- Ensure tool arguments are valid (e.g., post_id 1-100, user_id 1-10)
- Check MCP server logs for errors
- Verify JSONPlaceholder API is accessible

### Slow responses
- Check LLM API status
- Reduce `max_tokens` value
- Increase `temperature` for faster, less focused responses

## Development

### Running with Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Agent Logic

```python
from streamlit_agent.agent import AgentOrchestrator

agent = AgentOrchestrator(
    llm_provider="openai",
    llm_api_key="sk-...",
    llm_model="gpt-4o-mini",
    mcp_server_url="http://localhost:8000",
)

response, tools = agent.process_message(
    "Show me posts by user 1",
    conversation_history=[]
)
print(response)
```

## Code Quality

- ✅ **Type Hints** — Full type annotations throughout
- ✅ **Docstrings** — Comprehensive documentation
- ✅ **Logging** — Detailed operation logging
- ✅ **Error Handling** — Graceful error messages
- ✅ **Separation of Concerns** — Modular architecture

## Performance Notes

- **Streaming** — Responses stream token-by-token for better UX
- **Session State** — Conversation history maintained in memory
- **Tool Caching** — MCP tools fetched once and reused
- **Timeout** — 30-second timeout on MCP calls

## License

MIT License - See parent project

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify MCP server is running with `curl http://localhost:8000/health`
3. Test LLM API key directly: `python -c "from openai import OpenAI; ..."`
4. Check logs in terminal running Streamlit app
