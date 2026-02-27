"""MCP tools package for JSONPlaceholder API operations."""

from .posts import get_post_tool, list_posts_tool, get_comments_for_post_tool
from .users import get_user_tool, list_users_tool

__all__ = [
    "get_post_tool",
    "list_posts_tool",
    "get_comments_for_post_tool",
    "get_user_tool",
    "list_users_tool",
]
