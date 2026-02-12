"""Agent orchestration logic for LLM + MCP tool calling."""

import json
import logging
from typing import Any, Generator, Optional

from .llm_client import LLMClient
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates communication between LLM and MCP server.
    
    Handles:
    - Sending user messages to LLM
    - Detecting and parsing tool calls
    - Executing tools via MCP server
    - Managing conversation context
    - Streaming responses
    """

    def __init__(
        self,
        llm_provider: str,
        llm_api_key: str,
        llm_model: str,
        mcp_server_url: str,
        system_prompt: Optional[str] = None,
    ):
        """Initialize agent orchestrator.
        
        Args:
            llm_provider: LLM provider (openai, groq, huggingface)
            llm_api_key: API key for LLM
            llm_model: Model name/ID
            mcp_server_url: URL of MCP server
            system_prompt: Optional system prompt for LLM
        """
        self.llm = LLMClient.create(llm_provider, llm_api_key, llm_model)
        self.mcp = MCPClient(mcp_server_url)
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        logger.info(f"AgentOrchestrator initialized")
        logger.info(f"  LLM Provider: {llm_provider}")
        logger.info(f"  LLM Model: {llm_model}")
        logger.info(f"  MCP Server: {mcp_server_url}")

    def _default_system_prompt(self) -> str:
        """Get default system prompt for agent."""
        return """You are a helpful AI assistant with access to tools that can fetch data from JSONPlaceholder API.

You have access to the following tools:
- get_post(post_id): Get a specific post
- list_posts(user_id=None): List all posts or posts by a user
- get_comments_for_post(post_id): Get comments on a post
- get_user(user_id): Get user information
- list_users(): List all users

Always use tools to provide accurate information. Be conversational and helpful.
When using tools, briefly explain what you're doing before executing them."""

    def process_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]],
    ) -> tuple[str, Optional[list[dict[str, Any]]]]:
        """Process a user message, handling tool calls if needed.
        
        Args:
            user_message: The user's input message
            conversation_history: List of previous messages with role and content
            
        Returns:
            Tuple of (final_response, tool_calls_made)
            
        Raises:
            RuntimeError: If LLM or tool call fails
        """
        try:
            logger.info("Processing message with agent")
            
            # Add user message to history
            messages = conversation_history + [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ]
            
            # Get available tools from MCP server
            tools = self._get_mcp_tools()
            logger.info(f"Got {len(tools) if tools else 0} tools from MCP server")
            
            if not tools:
                logger.warning("No tools available from MCP server")
            
            # Send to LLM
            logger.info("Sending message to LLM with tools")
            response = self.llm.send_message(messages, tools=tools)
            logger.info(f"LLM response content: {response.get('content', '')[:100]}...")
            
            # Check if LLM requested tool calls
            tool_calls = self._extract_tool_calls(response)
            
            if tool_calls:
                logger.info(f"LLM requested {len(tool_calls)} tool calls")
                tool_results = self._execute_tool_calls(tool_calls)
                
                # Add assistant response with tool calls to history
                assistant_msg = {
                    "role": "assistant",
                    "content": response.get("content", ""),
                }
                messages.append(assistant_msg)
                
                # Add tool results
                for tool_call_id, result in tool_results.items():
                    messages.append({
                        "role": "user",
                        "content": f"Tool result: {json.dumps(result)}",
                    })
                
                # Get final response after tool execution
                logger.info("Getting final response after tool execution")
                final_response = self.llm.send_message(messages, tools=tools)
                
                return final_response.get("content", ""), tool_calls
            
            else:
                # No tool calls, return LLM response directly
                logger.info("No tool calls detected in LLM response")
                return response.get("content", ""), None
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise RuntimeError(f"Agent error: {str(e)}")

    def stream_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]],
    ) -> Generator[str, None, None]:
        """Stream a response for a user message with tool calling support.
        
        Args:
            user_message: The user's input message
            conversation_history: List of previous messages
            
        Yields:
            Response text chunks or tool call information
        """
        try:
            logger.info("Streaming message with agent")
            
            # Prepare messages
            messages = conversation_history + [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ]
            
            # Get available tools
            tools = self._get_mcp_tools()
            logger.info(f"Available tools for LLM: {[t.get('name') for t in tools]}")
            
            if not tools:
                logger.warning("No MCP tools available, streaming without tool support")
                for chunk in self.llm.stream_message(messages):
                    yield chunk
                return
            
            # Send to LLM with tools (don't stream yet, we need full response for tool calls)
            logger.info("Getting full response for tool call detection")
            response = self.llm.send_message(messages, tools=tools)
            
            # Check if LLM requested tool calls
            tool_calls = self._extract_tool_calls(response)
            
            if tool_calls:
                logger.info(f"Tool calls detected: {[t.get('name') for t in tool_calls]}")
                
                # Yield initial response content
                if response.get("content"):
                    yield response.get("content", "")
                    yield "\n\n"
                
                # Execute tools
                yield "🔧 Executing tools...\n"
                tool_results = self._execute_tool_calls(tool_calls)
                
                # Add assistant response with tool calls to history
                assistant_msg = {
                    "role": "assistant",
                    "content": response.get("content", ""),
                }
                messages.append(assistant_msg)
                
                # Add tool results
                for tool_call_id, result in tool_results.items():
                    messages.append({
                        "role": "user",
                        "content": f"Tool result: {json.dumps(result)}",
                    })
                
                # Get final response after tool execution
                logger.info("Getting final response after tool execution")
                yield "\n✅ Processing results...\n\n"
                
                # Stream final response
                for chunk in self.llm.stream_message(messages):
                    yield chunk
            
            else:
                logger.info("No tool calls detected, streaming response directly")
                # No tool calls, just stream the response
                for chunk in self.llm.stream_message(messages):
                    yield chunk
        
        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}")
            yield f"Error: {str(e)}"
            yield f"\n\n**Error**: {str(e)}"

    def _get_mcp_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server.
        
        Returns:
            List of tool definitions, or empty list if unavailable
        """
        try:
            tools = self.mcp.get_tools()
            logger.debug(f"Available MCP tools: {[t.get('name') for t in tools]}")
            return tools
        
        except Exception as e:
            logger.warning(f"Could not fetch tools: {str(e)}")
            return []

    def _extract_tool_calls(self, response: dict[str, Any]) -> Optional[list[dict[str, Any]]]:
        """Extract tool calls from LLM response.
        
        Args:
            response: Response from LLM.send_message()
            
        Returns:
            List of tool calls, or None if no tool calls
        """
        logger.debug(f"Raw response: {response}")
        logger.debug(f"Tool calls in response: {response.get('tool_calls')}")
        
        if not response.get("tool_calls"):
            logger.debug("No tool calls in response")
            return None
        
        tool_calls = response["tool_calls"]
        
        # Handle OpenAI/Groq format
        if hasattr(tool_calls, "__iter__"):
            parsed_calls = []
            for call in tool_calls:
                if hasattr(call, "function"):
                    # OpenAI format
                    parsed_calls.append({
                        "id": getattr(call, "id", str(len(parsed_calls))),
                        "name": call.function.name,
                        "arguments": json.loads(call.function.arguments) if isinstance(call.function.arguments, str) else call.function.arguments,
                    })
                    logger.info(f"Parsed tool call: {parsed_calls[-1]}")
            
            if parsed_calls:
                logger.info(f"Found {len(parsed_calls)} tool calls")
                return parsed_calls
        
        logger.debug("No tool calls found in response")
        return None

    def _execute_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute tool calls via MCP server.
        
        Args:
            tool_calls: List of tool calls to execute
            
        Returns:
            Dictionary mapping tool call IDs to results
        """
        results = {}
        
        for tool_call in tool_calls:
            tool_id = tool_call.get("id", tool_call.get("name"))
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})
            
            try:
                logger.info(f"Executing tool: {tool_name}")
                result = self.mcp.call_tool(tool_name, arguments)
                results[tool_id] = result
                logger.debug(f"Tool {tool_name} result: {result}")
            
            except Exception as e:
                logger.error(f"Tool execution failed for {tool_name}: {str(e)}")
                results[tool_id] = {"error": str(e)}
        
        return results

    def validate_mcp_connection(self) -> bool:
        """Validate connection to MCP server.
        
        Returns:
            True if MCP server is reachable
        """
        return self.mcp.health_check()

    def update_system_prompt(self, new_prompt: str) -> None:
        """Update the system prompt for the agent.
        
        Args:
            new_prompt: New system prompt
        """
        self.system_prompt = new_prompt
        logger.info("System prompt updated")
