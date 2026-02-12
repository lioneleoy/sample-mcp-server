"""MCP client for communicating with MCP HTTP servers."""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for communicating with MCP servers over HTTP.
    
    Handles tool calling and result retrieval from MCP endpoints.
    """

    def __init__(self, server_url: str, timeout: int = 30):
        """Initialize MCP client.
        
        Args:
            server_url: Base URL of the MCP server (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests package required")
        
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.requests = requests
        logger.info(f"MCPClient initialized for server: {server_url}")

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch available tools from MCP server.
        
        Returns:
            List of tool definitions from the server
            
        Raises:
            RuntimeError: If unable to fetch tools
        """
        try:
            logger.debug("Fetching tools from MCP server")
            
            # Mock tools for demonstration - in production, would fetch from server
            # For now, return expected tools that match the MCP server
            tools = [
                {
                    "name": "get_post",
                    "description": "Fetch a single post from JSONPlaceholder by post ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "post_id": {
                                "type": "integer",
                                "description": "Post ID (1-100)",
                                "minimum": 1,
                                "maximum": 100,
                            }
                        },
                        "required": ["post_id"],
                    }
                },
                {
                    "name": "list_posts",
                    "description": "Fetch all posts or posts by a specific user",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID (1-10)",
                                "minimum": 1,
                                "maximum": 10,
                            }
                        },
                        "required": [],
                    }
                },
                {
                    "name": "get_comments_for_post",
                    "description": "Fetch all comments for a specific post",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "post_id": {
                                "type": "integer",
                                "description": "Post ID (1-100)",
                                "minimum": 1,
                                "maximum": 100,
                            }
                        },
                        "required": ["post_id"],
                    }
                },
                {
                    "name": "get_user",
                    "description": "Fetch a single user by ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID (1-10)",
                                "minimum": 1,
                                "maximum": 10,
                            }
                        },
                        "required": ["user_id"],
                    }
                },
                {
                    "name": "list_users",
                    "description": "Fetch all users",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                },
            ]
            
            logger.info(f"Available tools: {[t['name'] for t in tools]}")
            return tools
        
        except Exception as e:
            logger.error(f"Error getting tools: {str(e)}")
            raise RuntimeError(f"Failed to fetch tools: {str(e)}")

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary
            
        Returns:
            Tool result as a dictionary
            
        Raises:
            RuntimeError: If tool call fails
        """
        try:
            logger.info(f"Calling tool: {tool_name} with args: {arguments}")
            
            # Prepare MCP-compatible request payload
            url = f"{self.server_url}/call_tool"
            
            payload = {
                "name": tool_name,
                "arguments": arguments,
            }
            
            response = self.requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code >= 400:
                error_msg = response.text
                logger.error(f"Tool call failed: {error_msg}")
                raise RuntimeError(f"Tool call failed: {error_msg}")
            
            result = response.json()
            logger.info(f"Tool {tool_name} executed successfully")
            logger.debug(f"Result: {result}")
            
            return result
        
        except self.requests.exceptions.Timeout:
            logger.error(f"Timeout calling tool {tool_name}")
            raise RuntimeError(f"Tool call timeout after {self.timeout}s")
        
        except self.requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            raise RuntimeError(f"Cannot reach MCP server at {self.server_url}")
        
        except Exception as e:
            logger.error(f"Tool call error: {str(e)}")
            raise RuntimeError(f"Tool call failed: {str(e)}")

    def health_check(self) -> bool:
        """Check if MCP server is healthy.
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            logger.debug("Checking MCP server health")
            
            url = f"{self.server_url}/health"
            response = self.requests.get(url, timeout=5)
            
            is_healthy = response.status_code == 200
            logger.info(f"MCP server health: {'OK' if is_healthy else 'UNAVAILABLE'}")
            
            return is_healthy
        
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False
