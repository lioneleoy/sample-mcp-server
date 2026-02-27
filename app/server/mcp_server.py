"""FastAPI-based server that exposes JSONPlaceholder API tools as HTTP endpoints."""

import logging
import sys
from typing import Any

from fastapi import Body, FastAPI, Request
from pydantic import BaseModel

from app.server.services.jsonplaceholder_client import JSONPlaceholderClient

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


class ToolCall(BaseModel):
    """Tool call request."""
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """Tool result response."""
    success: bool
    data: Any = None
    error: str = None


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root() -> list[dict[str, Any]]:
    """List available tools (root endpoint)."""
    return await list_tools()


@app.post("/")
async def handle_jsonrpc(payload: Any = Body(default=None)) -> dict[str, Any]:
    """Handle JSON-RPC 2.0 requests (MCP protocol)."""
    logger.info(f"POST / received payload: {payload}")
    logger.info(f"Payload type: {type(payload)}")
    
    if not isinstance(payload, dict):
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": None}
    
    logger.info(f"Payload keys: {list(payload.keys())}")
    
    jsonrpc_version = payload.get("jsonrpc")
    method = payload.get("method")
    params = payload.get("params", {})
    request_id = payload.get("id")
    
    if jsonrpc_version != "2.0":
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": request_id}
    
    logger.info(f"JSON-RPC method: {method}")
    
    # Handle MCP protocol methods
    if method == "initialize":
        requested_version = params.get("protocolVersion") if isinstance(params, dict) else None
        negotiated_version = (
            requested_version
            if requested_version in SUPPORTED_PROTOCOL_VERSIONS
            else SUPPORTED_PROTOCOL_VERSIONS[0]
        )

        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": negotiated_version,
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "jsonplaceholder-mcp-server",
                    "version": "1.0.0"
                }
            },
            "id": request_id
        }

    elif method == "notifications/initialized":
        return {
            "jsonrpc": "2.0",
            "result": {},
            "id": request_id,
        }
    
    elif method == "tools/list":
        tools = await list_tools()
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": tools
            },
            "id": request_id
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "Missing tool name"},
                "id": request_id
            }
        
        try:
            result = await call_tool(ToolCall(name=tool_name, arguments=arguments))
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": str(result.data)}] if result.success else [],
                    "isError": not result.success
                },
                "id": request_id
            }
        except Exception as e:
            logger.error(f"Tool execution error: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Tool execution failed: {str(e)}"},
                "id": request_id
            }
    
    else:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Method not found: {method}"},
            "id": request_id
        }


@app.post("/mcp")
async def handle_jsonrpc_mcp(payload: Any = Body(default=None)) -> dict[str, Any]:
    """Handle JSON-RPC 2.0 requests on /mcp for hosted platform compatibility."""
    return await handle_jsonrpc(payload)


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

