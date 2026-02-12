"""FastAPI-based server that exposes JSONPlaceholder API tools as HTTP endpoints."""

import logging
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.services.jsonplaceholder_client import JSONPlaceholderClient

logger = logging.getLogger(__name__)

app = FastAPI(
    title="JSONPlaceholder MCP Server",
    description="HTTP server exposing JSONPlaceholder API as tools",
)

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

