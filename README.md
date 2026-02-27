# JSONPlaceholder MCP Server - Production Ready

A production-grade Model Context Protocol (MCP) server implemented in Python that wraps the public JSONPlaceholder API. This server provides structured MCP tools for accessing posts, comments, and user data with proper error handling, validation, and logging.

## Features

- **5 Structured MCP Tools** — get_post, list_posts, get_comments_for_post, get_user, list_users
- **Full Type Safety** — Type hints throughout codebase, input validation on all tools
- **Robust Error Handling** — Network errors, timeouts, HTTP errors handled gracefully with structured responses
- **Production Logging** — Comprehensive logging at DEBUG, INFO, WARNING, and ERROR levels
- **Clean Architecture** — Separation of concerns: services layer (HTTP), tools layer (MCP definitions), and server layer
- **Managed Platform Ready** — Environment variable configuration, no hardcoded ports, 0.0.0.0 binding
- **Health Check Endpoint** — Built-in health verification method
- **Request Timeouts** — 10-second timeout on all API requests to prevent hanging
- **Async/Await** — Full async support for scalability

## Project Structure

```
app/
├── main.py                          # Entry point with environment configuration
└── server/
  ├── __init__.py                  # Server package initialization
  ├── mcp_server.py                # MCP server implementation with tool registration
  ├── services/
  │   ├── __init__.py
  │   └── jsonplaceholder_client.py # HTTP client with error handling
  └── tools/
    ├── __init__.py
    ├── posts.py                 # Post-related MCP tools
    └── users.py                 # User-related MCP tools
requirements.txt                      # Python dependencies
Procfile                             # Deployment start command
README.md                            # This file
.gitignore                           # Git ignore rules
```

## Installation

### Prerequisites

- Python 3.8+
- pip or poetry

### Local Setup

1. **Clone the repository:**
   ```bash
   cd /path/to/sample-mcp-server
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

## Running Locally

### Default Configuration

```bash
python -m app.main
```

The server will start on `0.0.0.0:8000` by default.

### Custom Host/Port

```bash
# Set environment variables before running
export HOST=127.0.0.1
export PORT=3000
python -m app.main
```

### With .env File

Create a `.env` file in the project root:

```bash
HOST=0.0.0.0
PORT=8000
```

Then run:
```bash
python -m app.main
```

## Available MCP Tools

### Posts Tools

#### `get_post`
Fetch a single post by ID.

**Input:**
```json
{
  "post_id": 1
}
```

**Output:**
```json
{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident...",
  "body": "quia et suscipit..."
}
```

#### `list_posts`
Fetch all posts, optionally filtered by user.

**Input:**
```json
{
  "user_id": 1
}
```

**Output:**
```json
{
  "data": [
    {
      "userId": 1,
      "id": 1,
      "title": "sunt aut facere repellat provident...",
      "body": "quia et suscipit..."
    }
  ],
  "count": 10
}
```

#### `get_comments_for_post`
Fetch all comments for a specific post.

**Input:**
```json
{
  "post_id": 1
}
```

**Output:**
```json
{
  "data": [
    {
      "postId": 1,
      "id": 1,
      "name": "id labore ex et quam laborum",
      "email": "Eliseo@gardner.biz",
      "body": "laudantium enim quasi est quidem magnam..."
    }
  ],
  "count": 5
}
```

### Users Tools

#### `get_user`
Fetch a single user by ID.

**Input:**
```json
{
  "user_id": 1
}
```

**Output:**
```json
{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  "address": {
    "street": "Kulas Light",
    "suite": "Apt. 556",
    "city": "Gwenborough",
    "zipcode": "92998-3874",
    "geo": {
      "lat": "-37.3159",
      "lng": "81.1496"
    }
  },
  "phone": "1-770-736-8031 x56442",
  "website": "hildegard.org",
  "company": {
    "name": "Romaguera-Crona",
    "catchPhrase": "Multi-layered client-server neural-net",
    "bs": "harness real-time e-markets"
  }
}
```

#### `list_users`
Fetch all users.

**Input:**
```json
{}
```

**Output:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Leanne Graham",
      "username": "Bret",
      "email": "Sincere@april.biz",
      ...
    }
  ],
  "count": 10
}
```

## Error Handling

All tools return structured error responses with status codes and messages:

```json
{
  "error": "Invalid post_id. Must be integer between 1 and 100",
  "status": 404
}
```

Common error scenarios:
- **Invalid Input** — Post/User ID out of valid range (1-100 for posts, 1-10 for users)
- **Not Found** — Requested resource doesn't exist (HTTP 404)
- **Network Error** — Connection failure or timeout
- **Parsing Error** — Invalid JSON response from API

## Architecture & Design Decisions

### Service Layer (`services/jsonplaceholder_client.py`)

The HTTP client is separate from MCP tool definitions, allowing:
- Easy testing of API calls independently
- Reusable HTTP logic across multiple tools
- Centralized error handling and logging
- Request timeout management (10 seconds)

**Design Pattern:** Context manager support for resource cleanup

### Tools Layer (`tools/posts.py`, `tools/users.py`)

Tools are defined with:
- **JSON Schema validation** — All inputs validated against MCP schema
- **Type hints** — Full type annotations for IDE support
- **Docstrings** — Comprehensive documentation for each tool
- **Async support** — Ready for high-concurrency scenarios
- **Structured responses** — JSON-formatted output, not raw text

**Design Pattern:** Tool definitions and execution handlers separated

### Server Layer (`server/mcp_server.py`)

The MCP server:
- Registers all tools at startup
- Routes tool calls to appropriate handlers
- Provides health check functionality
- Manages client lifecycle

**Design Pattern:** Handler registry pattern for tool execution

### Configuration (`main.py`)

- **Environment variables** — PORT and HOST from environment
- **Logging setup** — Structured logging to stdout
- **Async runtime** — asyncio.run() for server execution
- **Error handling** — Graceful shutdown and error reporting

## Deployment on Natoma Security Platform

This server is compatible with Natoma-managed hosting requirements:

- Binds to `0.0.0.0` by default
- Honors injected `PORT` environment variable
- Exposes `/health` endpoint for liveness checks
- Uses stdout logging for platform log collection

### Steps

1. **Configure service runtime:**
  - Runtime: Python 3.11+
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `python -m app.main`

2. **Set Environment Variables (if required by your workspace):**
  - `PORT` — Usually platform-injected
  - `HOST` — Leave unset (defaults to `0.0.0.0`) or set explicitly
  - `LOG_LEVEL` — Optional (`INFO`, `DEBUG`, `WARNING`, `ERROR`)

3. **Set health-check path:**
  - `/health`

## Deployment on Render

### Steps

1. **Create a new Web Service on Render:**
   - Repository: Your Git repo URL
   - Runtime: Python 3.11
   - Build Command: `pip install -r requirements.txt`
   - Start Command: Use the Procfile (automatically detected)

2. **Set Environment Variables (Optional):**
   - `PORT` — Automatically set by Render, no need to configure
   - `HOST` — Keep as `0.0.0.0` for Render
   - Other custom variables if needed

3. **Deploy:**
   - Render will automatically use the Procfile
   - Service will start on `web: python -m app.main`

### Health Check

Render can verify server health by calling the built-in health check:

```python
# Server includes async health_check() method
# Returns: {"status": "healthy", "server": "online", "api": "connected"}
```

## Development & Testing

### Running Tests (Manual)

```bash
# Test a single tool via Python
python -c "
from app.server.services import JSONPlaceholderClient

client = JSONPlaceholderClient()
post = client.get_post(1)
print(post)
"
```

### Debugging

Set log level to DEBUG:

```python
# In main.py or your test script
logging.basicConfig(level=logging.DEBUG)
```

### Code Quality

- **Type checking:** Use `mypy` for static type checking
- **Linting:** Use `pylint` or `flake8`
- **Code formatting:** Use `black` for consistent style

```bash
# Example type check
mypy app/
```

## API Reference

### JSONPlaceholderClient Methods

All methods include:
- Type hints for parameters and return values
- Comprehensive docstrings
- Error handling with logging
- Timeout support (default 10 seconds)

```python
from app.server.services import JSONPlaceholderClient

client = JSONPlaceholderClient()

# Posts
post = client.get_post(1)  # Returns dict or None
posts = client.list_posts(user_id=1)  # Returns list
comments = client.get_comments_for_post(1)  # Returns list

# Users
user = client.get_user(1)  # Returns dict or None
users = client.list_users()  # Returns list
```

## Production Considerations

✅ **Security:**
- No hardcoded credentials
- Input validation on all parameters
- Type hints prevent many injection attacks

✅ **Reliability:**
- Comprehensive error handling
- Request timeouts prevent hangs
- Graceful degradation on API failures
- Health check for monitoring

✅ **Scalability:**
- Async/await support
- Clean separation of concerns
- Logging for observability
- Standard HTTP transport

✅ **Maintainability:**
- Full type hints
- Detailed docstrings
- Clean code structure
- Inline comments on design decisions

## Troubleshooting

### Server won't start
- Check PORT is not in use: `lsof -i :8000`
- Verify Python 3.8+: `python --version`
- Check dependencies: `pip list | grep mcp`

### API calls failing
- Verify JSONPlaceholder is accessible: `curl https://jsonplaceholder.typicode.com/posts/1`
- Check firewall/network settings
- Review logs for timeout messages

### Invalid tool responses
- Verify tool input matches schema (post_id 1-100, user_id 1-10)
- Check logs for validation errors
- Ensure JSONPlaceholder API response format hasn't changed

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the logs: `python -m app.main` shows all operations
2. Test API directly: `curl https://jsonplaceholder.typicode.com/posts/1`
3. Verify configuration with `echo $PORT $HOST`
