"""MCP tools for user-related operations on JSONPlaceholder API."""

import logging
from typing import Any, List

from mcp.types import TextContent, Tool

# Configure logging
logger = logging.getLogger(__name__)


def get_user_tool() -> Tool:
    """
    Create MCP tool definition for fetching a single user.
    
    Returns:
        Tool specification that can be registered with MCP server
    """
    return Tool(
        name="get_user",
        description="Fetch a single user from JSONPlaceholder by user ID. Returns user details including name, email, and contact information.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The ID of the user to fetch (positive integer between 1-10)",
                    "minimum": 1,
                    "maximum": 10,
                }
            },
            "required": ["user_id"],
        },
    )


def list_users_tool() -> Tool:
    """
    Create MCP tool definition for fetching all users.
    
    Returns:
        Tool specification that can be registered with MCP server
    """
    return Tool(
        name="list_users",
        description="Fetch all users from JSONPlaceholder. Returns a list of users with names, emails, and contact information.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )


async def execute_get_user(client: Any, user_id: int) -> List[TextContent]:
    """
    Execute the get_user tool: fetch a single user by ID.
    
    Args:
        client: JSONPlaceholderClient instance
        user_id: The ID of the user to fetch
        
    Returns:
        List containing TextContent with user data or error message
    """
    # Validate input
    if not isinstance(user_id, int) or user_id < 1 or user_id > 10:
        logger.warning(f"Invalid user_id: {user_id}")
        return [
            TextContent(
                type="text",
                text='{"error": "Invalid user_id. Must be integer between 1 and 10"}',
            )
        ]

    try:
        logger.info(f"Fetching user {user_id}")
        user = client.get_user(user_id)

        if user is None:
            logger.info(f"User {user_id} not found")
            return [
                TextContent(
                    type="text",
                    text=f'{{"error": "User {user_id} not found", "status": 404}}',
                )
            ]

        # Return structured user data
        import json

        logger.info(f"Successfully retrieved user {user_id}")
        return [TextContent(type="text", text=json.dumps(user))]

    except ValueError as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "{str(e)}"}}')]
    except Exception as e:
        logger.error(f"Unexpected error fetching user {user_id}: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "Internal server error"}}')]


async def execute_list_users(client: Any) -> List[TextContent]:
    """
    Execute the list_users tool: fetch all users.
    
    Args:
        client: JSONPlaceholderClient instance
        
    Returns:
        List containing TextContent with users data or error message
    """
    try:
        logger.info("Fetching all users")
        users = client.list_users()

        if not users:
            logger.warning("No users found")
            return [
                TextContent(
                    type="text",
                    text='{"data": [], "message": "No users found"}',
                )
            ]

        # Return structured users data
        import json

        logger.info(f"Successfully retrieved {len(users)} users")
        return [TextContent(type="text", text=json.dumps({"data": users, "count": len(users)}))]

    except ValueError as e:
        logger.error(f"Error fetching users: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "{str(e)}"}}')]
    except Exception as e:
        logger.error(f"Unexpected error fetching users: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "Internal server error"}}')]
