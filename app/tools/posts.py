"""MCP tools for post-related operations on JSONPlaceholder API."""

import logging
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

# Configure logging
logger = logging.getLogger(__name__)


def get_post_tool() -> Tool:
    """
    Create MCP tool definition for fetching a single post.
    
    Returns:
        Tool specification that can be registered with MCP server
    """
    return Tool(
        name="get_post",
        description="Fetch a single post from JSONPlaceholder by post ID. Returns post details including title and body.",
        inputSchema={
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "integer",
                    "description": "The ID of the post to fetch (positive integer between 1-100)",
                    "minimum": 1,
                    "maximum": 100,
                }
            },
            "required": ["post_id"],
        },
    )


def list_posts_tool() -> Tool:
    """
    Create MCP tool definition for fetching all posts.
    
    Returns:
        Tool specification that can be registered with MCP server
    """
    return Tool(
        name="list_posts",
        description="Fetch all posts from JSONPlaceholder. Optionally filter by user ID. Returns a list of posts with titles and bodies.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "Optional user ID to filter posts by (positive integer between 1-10)",
                    "minimum": 1,
                    "maximum": 10,
                }
            },
            "required": [],
        },
    )


def get_comments_for_post_tool() -> Tool:
    """
    Create MCP tool definition for fetching comments on a post.
    
    Returns:
        Tool specification that can be registered with MCP server
    """
    return Tool(
        name="get_comments_for_post",
        description="Fetch all comments for a specific post from JSONPlaceholder. Returns a list of comments with names, emails, and bodies.",
        inputSchema={
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "integer",
                    "description": "The ID of the post to fetch comments for (positive integer between 1-100)",
                    "minimum": 1,
                    "maximum": 100,
                }
            },
            "required": ["post_id"],
        },
    )


async def execute_get_post(client: Any, post_id: int) -> List[TextContent]:
    """
    Execute the get_post tool: fetch a single post by ID.
    
    Args:
        client: JSONPlaceholderClient instance
        post_id: The ID of the post to fetch
        
    Returns:
        List containing TextContent with post data or error message
    """
    # Validate input
    if not isinstance(post_id, int) or post_id < 1 or post_id > 100:
        logger.warning(f"Invalid post_id: {post_id}")
        return [
            TextContent(
                type="text",
                text='{"error": "Invalid post_id. Must be integer between 1 and 100"}',
            )
        ]

    try:
        logger.info(f"Fetching post {post_id}")
        post = client.get_post(post_id)

        if post is None:
            logger.info(f"Post {post_id} not found")
            return [
                TextContent(
                    type="text",
                    text=f'{{"error": "Post {post_id} not found", "status": 404}}',
                )
            ]

        # Return structured post data
        import json

        logger.info(f"Successfully retrieved post {post_id}")
        return [TextContent(type="text", text=json.dumps(post))]

    except ValueError as e:
        logger.error(f"Error fetching post {post_id}: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "{str(e)}"}}')]
    except Exception as e:
        logger.error(f"Unexpected error fetching post {post_id}: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "Internal server error"}}')]


async def execute_list_posts(client: Any, user_id: int | None = None) -> List[TextContent]:
    """
    Execute the list_posts tool: fetch all posts, optionally filtered by user.
    
    Args:
        client: JSONPlaceholderClient instance
        user_id: Optional user ID to filter posts by
        
    Returns:
        List containing TextContent with posts data or error message
    """
    # Validate input
    if user_id is not None:
        if not isinstance(user_id, int) or user_id < 1 or user_id > 10:
            logger.warning(f"Invalid user_id: {user_id}")
            return [
                TextContent(
                    type="text",
                    text='{"error": "Invalid user_id. Must be integer between 1 and 10"}',
                )
            ]

    try:
        filter_text = f" for user {user_id}" if user_id else ""
        logger.info(f"Fetching posts{filter_text}")
        posts = client.list_posts(user_id=user_id)

        if not posts:
            logger.warning(f"No posts found{filter_text}")
            return [
                TextContent(
                    type="text",
                    text=f'{{"data": [], "message": "No posts found{filter_text}"}}',
                )
            ]

        # Return structured posts data
        import json

        logger.info(f"Successfully retrieved {len(posts)} posts{filter_text}")
        return [TextContent(type="text", text=json.dumps({"data": posts, "count": len(posts)}))]

    except ValueError as e:
        logger.error(f"Error fetching posts: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "{str(e)}"}}')]
    except Exception as e:
        logger.error(f"Unexpected error fetching posts: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "Internal server error"}}')]


async def execute_get_comments_for_post(client: Any, post_id: int) -> List[TextContent]:
    """
    Execute the get_comments_for_post tool: fetch comments for a specific post.
    
    Args:
        client: JSONPlaceholderClient instance
        post_id: The ID of the post to fetch comments for
        
    Returns:
        List containing TextContent with comments data or error message
    """
    # Validate input
    if not isinstance(post_id, int) or post_id < 1 or post_id > 100:
        logger.warning(f"Invalid post_id: {post_id}")
        return [
            TextContent(
                type="text",
                text='{"error": "Invalid post_id. Must be integer between 1 and 100"}',
            )
        ]

    try:
        logger.info(f"Fetching comments for post {post_id}")
        comments = client.get_comments_for_post(post_id)

        if not comments:
            logger.info(f"No comments found for post {post_id}")
            return [
                TextContent(
                    type="text",
                    text=f'{{"data": [], "message": "No comments found for post {post_id}"}}',
                )
            ]

        # Return structured comments data
        import json

        logger.info(f"Successfully retrieved {len(comments)} comments for post {post_id}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"data": comments, "count": len(comments)}),
            )
        ]

    except ValueError as e:
        logger.error(f"Error fetching comments for post {post_id}: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "{str(e)}"}}')]
    except Exception as e:
        logger.error(f"Unexpected error fetching comments for post {post_id}: {str(e)}")
        return [TextContent(type="text", text=f'{{"error": "Internal server error"}}')]
