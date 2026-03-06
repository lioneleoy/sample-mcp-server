"""FastAPI-based server that exposes JSONPlaceholder API tools as HTTP endpoints."""

import asyncio
import json
import logging
import sys
from uuid import uuid4
from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

try:
    from app.server.services.jsonplaceholder_client import JSONPlaceholderClient
except ModuleNotFoundError:
    from server.services.jsonplaceholder_client import JSONPlaceholderClient

# Configure logging to ensure it outputs to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)

SUPPORTED_PROTOCOL_VERSIONS = [
    "2025-11-05",
    "2025-06-18",
    "2025-03-26",
]

SESSION_ID_HEADER_NAME = "mcp-session-id"

app = FastAPI(
    title="JSONPlaceholder MCP Server",
    description="HTTP server exposing JSONPlaceholder API as tools",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"🔵 {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    response = await call_next(request)
    logger.info(f"🟢 {request.method} {request.url.path} → {response.status_code}")
    return response


# Initialize client
client = JSONPlaceholderClient(timeout=10)
active_sessions: set[str] = set()


class ToolCall(BaseModel):
    """Tool call request."""
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """Tool result response."""
    success: bool
    data: Any = None
    error: str | None = None


def _jsonrpc_error(code: int, message: str, request_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "error": {"code": code, "message": message},
        "id": request_id,
    }


async def _handle_jsonrpc_request(
    payload: Any,
    session_id: str | None,
) -> tuple[dict[str, Any], int, str | None]:
    if not isinstance(payload, dict):
        return _jsonrpc_error(-32600, "Invalid Request", None), 400, None

    jsonrpc_version = payload.get("jsonrpc")
    method = payload.get("method")
    params = payload.get("params", {})
    request_id = payload.get("id")

    if jsonrpc_version != "2.0":
        return _jsonrpc_error(-32600, "Invalid Request", request_id), 400, None

    logger.info(f"JSON-RPC method: {method}")

    if method == "initialize":
        requested_version = params.get("protocolVersion") if isinstance(params, dict) else None
        negotiated_version = (
            requested_version
            if requested_version in SUPPORTED_PROTOCOL_VERSIONS
            else SUPPORTED_PROTOCOL_VERSIONS[0]
        )

        assigned_session = session_id if session_id in active_sessions else str(uuid4())
        active_sessions.add(assigned_session)

        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": negotiated_version,
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "jsonplaceholder-mcp-server",
                    "version": "1.0.0",
                },
            },
            "id": request_id,
        }, 200, assigned_session

    if method in {"notifications/initialized", "tools/list", "tools/call"}:
        if session_id and session_id not in active_sessions:
            return _jsonrpc_error(-32000, "Bad Request: invalid session ID or method.", request_id), 400, None

    if method == "notifications/initialized":
        return {
            "jsonrpc": "2.0",
            "result": {},
            "id": request_id,
        }, 200, None

    if method == "tools/list":
        tools = await list_tools()
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": tools,
            },
            "id": request_id,
        }, 200, None

    if method == "tools/call":
        if not isinstance(params, dict):
            return _jsonrpc_error(-32602, "Invalid params", request_id), 400, None

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            return _jsonrpc_error(-32602, "Missing tool name", request_id), 400, None

        try:
            result = await call_tool(ToolCall(name=tool_name, arguments=arguments))
            content = []
            if result.success:
                content = [{"type": "text", "text": json.dumps(result.data, default=str)}]

            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": content,
                    "isError": not result.success,
                },
                "id": request_id,
            }, 200, None
        except Exception as exc:
            logger.error(f"Tool execution error: {str(exc)}")
            return _jsonrpc_error(-32603, f"Tool execution failed: {str(exc)}", request_id), 500, None

    return _jsonrpc_error(-32601, f"Method not found: {method}", request_id), 404, None


async def _handle_jsonrpc_payload(
    payload: Any,
    session_id: str | None,
) -> tuple[Any, int, str | None]:
    if isinstance(payload, list):
        if not payload:
            return _jsonrpc_error(-32600, "Invalid Request", None), 400, None

        responses: list[dict[str, Any]] = []
        assigned_session: str | None = None
        effective_session = session_id
        worst_status = 200

        for item in payload:
            body, status, new_session = await _handle_jsonrpc_request(item, effective_session)
            if status >= 400:
                worst_status = status

            if new_session and not assigned_session:
                assigned_session = new_session
                effective_session = new_session

            if isinstance(item, dict) and item.get("id") is None and "result" in body:
                continue

            responses.append(body)

        if not responses:
            return {}, 200, assigned_session

        return responses, worst_status, assigned_session

    return await _handle_jsonrpc_request(payload, session_id)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root() -> list[dict[str, Any]]:
    """List available tools (root endpoint)."""
    return await list_tools()


@app.post("/")
async def handle_jsonrpc(request: Request, payload: Any = Body(default=None)) -> JSONResponse:
    """Handle JSON-RPC 2.0 requests (MCP protocol)."""
    logger.info(f"POST / received payload: {payload}")
    logger.info(f"Payload type: {type(payload)}")
    session_id = request.headers.get(SESSION_ID_HEADER_NAME)
    response_body, status_code, assigned_session = await _handle_jsonrpc_payload(payload, session_id)

    response_headers: dict[str, str] = {}
    if assigned_session:
        response_headers[SESSION_ID_HEADER_NAME] = assigned_session

    return JSONResponse(content=response_body, status_code=status_code, headers=response_headers)


@app.post("/mcp")
async def handle_jsonrpc_mcp(request: Request, payload: Any = Body(default=None)) -> JSONResponse:
    """Handle JSON-RPC 2.0 requests on /mcp for hosted platform compatibility."""
    session_id = request.headers.get(SESSION_ID_HEADER_NAME)
    response_body, status_code, assigned_session = await _handle_jsonrpc_payload(payload, session_id)

    response_headers: dict[str, str] = {}
    if assigned_session:
        response_headers[SESSION_ID_HEADER_NAME] = assigned_session

    return JSONResponse(content=response_body, status_code=status_code, headers=response_headers)


@app.get("/mcp")
async def handle_mcp_stream(request: Request):
    """Provide a lightweight SSE stream endpoint for Streamable HTTP MCP clients."""
    session_id = request.headers.get(SESSION_ID_HEADER_NAME)
    if not session_id or session_id not in active_sessions:
        return JSONResponse(
            content=_jsonrpc_error(-32000, "Bad Request: invalid session ID or method.", None),
            status_code=400,
        )

    async def event_stream():
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/message",
            "params": {
                "level": "info",
                "data": "SSE stream ready",
            },
        }
        yield f"event: message\\ndata: {json.dumps(notification)}\\n\\n"

        for _ in range(3):
            await asyncio.sleep(5)
            yield ": keep-alive\\n\\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/tools")
async def list_tools() -> list[dict[str, Any]]:
    """List available tools."""
    return [
        {
            "name": "get_post",
            "description": "Get a specific post by ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "integer",
                        "description": "Post ID (1-100)",
                    }
                },
                "required": ["post_id"],
            },
        },
        {
            "name": "list_posts",
            "description": "List all posts or posts by a specific user",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "Optional user ID to filter posts",
                    }
                },
                "required": [],
            },
        },
        {
            "name": "get_comments_for_post",
            "description": "Get all comments on a specific post",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "integer",
                        "description": "Post ID",
                    }
                },
                "required": ["post_id"],
            },
        },
        {
            "name": "get_user",
            "description": "Get user information by ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "User ID (1-10)",
                    }
                },
                "required": ["user_id"],
            },
        },
        {
            "name": "list_users",
            "description": "List all users",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


@app.post("/call_tool")
async def call_tool(request: ToolCall) -> ToolResult:
    """Call a tool and return the result."""
    try:
        logger.info(f"Calling tool: {request.name} with args: {request.arguments}")

        if request.name == "get_post":
            post_id = request.arguments.get("post_id")
            if not isinstance(post_id, int) or post_id < 1 or post_id > 100:
                raise ValueError("post_id must be an integer between 1 and 100")
            result = client.get_post(post_id)

        elif request.name == "list_posts":
            user_id = request.arguments.get("user_id")
            result = client.list_posts(user_id)

        elif request.name == "get_comments_for_post":
            post_id = request.arguments.get("post_id")
            if not isinstance(post_id, int):
                raise ValueError("post_id must be an integer")
            result = client.get_comments_for_post(post_id)

        elif request.name == "get_user":
            user_id = request.arguments.get("user_id")
            if not isinstance(user_id, int) or user_id < 1 or user_id > 10:
                raise ValueError("user_id must be an integer between 1 and 10")
            result = client.get_user(user_id)

        elif request.name == "list_users":
            result = client.list_users()

        else:
            raise ValueError(f"Unknown tool: {request.name}")

        return ToolResult(success=True, data=result)

    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        return ToolResult(success=False, error=str(e))

