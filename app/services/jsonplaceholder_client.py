"""HTTP client for JSONPlaceholder API with error handling and type safety."""

import logging
import requests
from typing import Any, Dict, List, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://jsonplaceholder.typicode.com"
REQUEST_TIMEOUT = 10  # seconds
DEFAULT_RETRIES = 1


class JSONPlaceholderClient:
    """
    Client for interacting with the JSONPlaceholder API.
    
    Provides typed methods for fetching posts, users, and comments with
    proper error handling, logging, and timeout management.
    """

    def __init__(self, base_url: str = BASE_URL, timeout: int = REQUEST_TIMEOUT):
        """
        Initialize the JSONPlaceholder API client.
        
        Args:
            base_url: The base URL for the JSONPlaceholder API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        logger.info(f"JSONPlaceholderClient initialized with base_url={base_url}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Make an HTTP request to the JSONPlaceholder API.
        
        Handles network errors, timeouts, and HTTP error codes gracefully.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., "/posts/1")
            params: Query parameters for the request
            
        Returns:
            Parsed JSON response, or None if request fails
            
        Raises:
            ValueError: If the request fails after retries
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.debug(f"Making {method} request to {url} with params={params}")
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.timeout,
            )

            # Handle HTTP error codes
            if response.status_code == 404:
                logger.warning(f"Resource not found: {url}")
                return None

            if response.status_code >= 400:
                logger.error(
                    f"HTTP error {response.status_code} for {url}: {response.text}"
                )
                raise ValueError(
                    f"HTTP {response.status_code}: {response.reason}"
                )

            # Successfully parse JSON response
            data = response.json()
            logger.debug(f"Successfully retrieved data from {url}")
            return data

        except Timeout:
            logger.error(f"Request timeout after {self.timeout}s for {url}")
            raise ValueError(f"Request timeout after {self.timeout} seconds")

        except ConnectionError as e:
            logger.error(f"Connection error for {url}: {str(e)}")
            raise ValueError(f"Failed to connect to JSONPlaceholder API: {str(e)}")

        except RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            raise ValueError(f"API request failed: {str(e)}")

        except ValueError as e:
            logger.error(f"JSON parsing error for {url}: {str(e)}")
            raise ValueError(f"Invalid JSON response from API")

    def get_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single post by ID.
        
        Args:
            post_id: The ID of the post to fetch
            
        Returns:
            Post dictionary with id, userId, title, body, or None if not found
        """
        return self._make_request("GET", f"/posts/{post_id}")

    def list_posts(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all posts, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter posts by
            
        Returns:
            List of post dictionaries, or empty list if request fails
        """
        params = {"userId": user_id} if user_id else None
        result = self._make_request("GET", "/posts", params=params)
        return result if isinstance(result, list) else []

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single user by ID.
        
        Args:
            user_id: The ID of the user to fetch
            
        Returns:
            User dictionary with id, name, username, email, etc., or None if not found
        """
        return self._make_request("GET", f"/users/{user_id}")

    def list_users(self) -> List[Dict[str, Any]]:
        """
        Fetch all users.
        
        Returns:
            List of user dictionaries, or empty list if request fails
        """
        result = self._make_request("GET", "/users")
        return result if isinstance(result, list) else []

    def get_comments_for_post(self, post_id: int) -> List[Dict[str, Any]]:
        """
        Fetch all comments for a specific post.
        
        Args:
            post_id: The ID of the post to fetch comments for
            
        Returns:
            List of comment dictionaries, or empty list if request fails
        """
        params = {"postId": post_id}
        result = self._make_request("GET", "/comments", params=params)
        return result if isinstance(result, list) else []

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
        logger.info("JSONPlaceholderClient session closed")

    def __enter__(self) -> "JSONPlaceholderClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
