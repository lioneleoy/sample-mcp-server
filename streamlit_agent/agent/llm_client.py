"""LLM client abstraction supporting OpenAI, Groq, and Hugging Face."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model: str):
        """Initialize LLM client.
        
        Args:
            api_key: API key for the provider
            model: Model name/ID
        """
        self.api_key = api_key
        self.model = model

    @staticmethod
    def _clean_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Clean messages by removing null/empty tool_calls fields.
        
        Some LLM providers (like Groq) don't accept null values in tool_calls.
        This ensures messages are properly formatted.
        
        Args:
            messages: List of message dicts
            
        Returns:
            Cleaned message list
        """
        cleaned = []
        for msg in messages:
            clean_msg = {k: v for k, v in msg.items() if v is not None and (k != "tool_calls" or v)}
            if "role" in clean_msg and "content" in clean_msg:
                cleaned.append(clean_msg)
        return cleaned

    @abstractmethod
    def send_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a message to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            LLM response with choices, tool calls, etc.
        """
        pass

    @abstractmethod
    def stream_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream a message from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            **kwargs: Additional parameters
            
        Yields:
            Response text chunks
        """
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client with tool support."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o-mini)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)
        logger.info(f"OpenAI client initialized with model: {model}")

    def send_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send message to OpenAI API.
        
        Args:
            messages: Message list
            tools: Tool definitions in JSON schema format
            **kwargs: Additional parameters
            
        Returns:
            Response with choices and tool calls
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }
            
            if tools:
                params["tools"] = [{"type": "function", "function": tool} for tool in tools]
            
            response = self.client.chat.completions.create(**params)
            
            logger.debug(f"OpenAI response: {response.choices[0].finish_reason}")
            
            return {
                "content": response.choices[0].message.content or "",
                "tool_calls": getattr(response.choices[0].message, "tool_calls", None),
                "finish_reason": response.choices[0].finish_reason,
            }
        
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def stream_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream message from OpenAI API.
        
        Args:
            messages: Message list
            tools: Tool definitions
            **kwargs: Additional parameters
            
        Yields:
            Text chunks from response
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": True,
            }
            
            if tools:
                params["tools"] = [{"type": "function", "function": tool} for tool in tools]
            
            with self.client.chat.completions.create(**params) as stream:
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise


class GroqClient(BaseLLMClient):
    """Groq API client with tool support."""

    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        """Initialize Groq client.
        
        Args:
            api_key: Groq API key
            model: Model name (default: mixtral-8x7b-32768)
        """
        try:
            import groq
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")
        
        super().__init__(api_key, model)
        self.client = groq.Groq(api_key=api_key)
        logger.info(f"Groq client initialized with model: {model}")

    def send_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send message to Groq API."""
        try:
            # Clean messages to remove null tool_calls (Groq doesn't accept null values)
            clean_msgs = self._clean_messages(messages)
            
            params = {
                "model": self.model,
                "messages": clean_msgs,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
            }
            
            if tools:
                params["tools"] = [{"type": "function", "function": tool} for tool in tools]
            
            response = self.client.chat.completions.create(**params)
            
            logger.debug(f"Groq response finish_reason: {response.choices[0].finish_reason}")
            logger.debug(f"Groq response message: {response.choices[0].message}")
            logger.debug(f"Groq response tool_calls: {getattr(response.choices[0].message, 'tool_calls', None)}")
            
            return {
                "content": response.choices[0].message.content or "",
                "tool_calls": getattr(response.choices[0].message, "tool_calls", None),
                "finish_reason": response.choices[0].finish_reason,
            }
        
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise

    def stream_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream message from Groq API."""
        try:
            # Clean messages to remove null tool_calls
            clean_msgs = self._clean_messages(messages)
            
            params = {
                "model": self.model,
                "messages": clean_msgs,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2048),
                "stream": True,
            }
            
            if tools:
                params["tools"] = [{"type": "function", "function": tool} for tool in tools]
            
            with self.client.chat.completions.create(**params) as stream:
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"Groq streaming error: {str(e)}")
            raise


class HuggingFaceClient(BaseLLMClient):
    """Hugging Face Inference API client."""

    def __init__(self, api_key: str, model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"):
        """Initialize Hugging Face client.
        
        Args:
            api_key: HF API key
            model: Model name/ID
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests package required")
        
        super().__init__(api_key, model)
        self.base_url = "https://api-inference.huggingface.co/models"
        logger.info(f"Hugging Face client initialized with model: {model}")

    def send_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send message to Hugging Face API."""
        try:
            import requests
            
            prompt = self._format_prompt(messages)
            
            url = f"{self.base_url}/{self.model}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_new_tokens": kwargs.get("max_tokens", 512),
                    "top_p": 0.95,
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            text = result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
            
            logger.debug(f"HuggingFace response received")
            
            return {
                "content": text,
                "tool_calls": None,
                "finish_reason": "stop",
            }
        
        except Exception as e:
            logger.error(f"Hugging Face API error: {str(e)}")
            raise

    def stream_message(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream message from Hugging Face API."""
        try:
            import requests
            
            prompt = self._format_prompt(messages)
            
            url = f"{self.base_url}/{self.model}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            payload = {
                "inputs": prompt,
                "stream": True,
                "parameters": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_new_tokens": kwargs.get("max_tokens", 512),
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "token" in data and "text" in data["token"]:
                        yield data["token"]["text"]
        
        except Exception as e:
            logger.error(f"Hugging Face streaming error: {str(e)}")
            raise

    def _format_prompt(self, messages: list[dict[str, str]]) -> str:
        """Format messages as a single prompt string."""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant: "
        return prompt


class LLMClient:
    """Factory class for creating LLM clients."""

    @staticmethod
    def create(provider: str, api_key: str, model: str) -> BaseLLMClient:
        """Create LLM client based on provider.
        
        Args:
            provider: Provider name (openai, groq, huggingface)
            api_key: API key for the provider
            model: Model name
            
        Returns:
            Initialized LLM client
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower().strip()
        
        if provider == "openai":
            return OpenAIClient(api_key, model)
        elif provider == "groq":
            return GroqClient(api_key, model)
        elif provider == "huggingface":
            return HuggingFaceClient(api_key, model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. Use: openai, groq, huggingface")
