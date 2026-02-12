"""
Streamlit AI Agent Application for JSONPlaceholder API

A production-ready Streamlit application that acts as an AI agent
with access to tools that query the JSONPlaceholder API via an MCP server.

Features:
- Multi-provider LLM support (OpenAI, Groq, Hugging Face)
- Streaming responses with real-time token display
- Tool call indicators and execution feedback
- Configurable system prompt and model parameters
- Conversation memory with session state
- Health check monitoring
"""

import logging
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from agent import AgentOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Agent - JSONPlaceholder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .tool-call {
        background-color: #f0f2f6;
        border-left: 4px solid #0066cc;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        font-family: monospace;
    }
    .error-box {
        background-color: #ffe6e6;
        border-left: 4px solid #cc0000;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    </style>
    """, unsafe_allow_html=True)


def load_config() -> dict:
    """Load configuration from environment variables and Streamlit secrets.
    
    Returns:
        Configuration dictionary with LLM and MCP settings
    """
    config = {
        "llm_provider": os.environ.get("LLM_PROVIDER", "openai").lower(),
        "llm_api_key": os.environ.get("LLM_API_KEY", ""),
        "llm_model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        "mcp_server_url": os.environ.get("MCP_SERVER_URL", "http://localhost:8000"),
    }
    
    # Allow Streamlit secrets to override environment variables (if available)
    try:
        if "llm_api_key" in st.secrets:
            config["llm_api_key"] = st.secrets["llm_api_key"]
        if "mcp_server_url" in st.secrets:
            config["mcp_server_url"] = st.secrets["mcp_server_url"]
    except Exception:
        # Secrets file doesn't exist - that's fine, use environment variables
        pass
    
    return config


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    if "agent_error" not in st.session_state:
        st.session_state.agent_error = None
    
    if "mcp_health" not in st.session_state:
        st.session_state.mcp_health = None
    
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = None


def render_sidebar() -> dict:
    """Render sidebar configuration panel.
    
    Returns:
        Dictionary with user configuration settings
    """
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Load configuration
        config = load_config()
        
        st.subheader("LLM Settings")
        
        # LLM Provider selection
        provider = st.selectbox(
            "LLM Provider",
            ["openai", "groq", "huggingface"],
            index=0 if config["llm_provider"] == "openai" else (1 if config["llm_provider"] == "groq" else 2),
            help="Select the LLM provider to use",
        )
        
        # API Key status
        api_key = config.get("llm_api_key", "")
        if api_key:
            st.success(f"✅ API key loaded ({len(api_key)} chars)")
        else:
            st.warning("⚠️ No API key found. Set in .env or environment variables.")
        
        # Model selection
        model_options = {
            "openai": ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
            "groq": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "llama-3.3-70b-specdec"],
            "huggingface": ["mistralai/Mixtral-8x7B-Instruct-v0.1"],
        }
        
        selected_model = st.selectbox(
            "Model",
            model_options.get(provider, []),
            help="Select the model to use",
        )
        
        st.divider()
        st.subheader("MCP Server")
        
        # MCP Server URL
        mcp_url = st.text_input(
            "MCP Server URL",
            value=config.get("mcp_server_url", "http://localhost:8000"),
            help="URL of the MCP server (e.g., http://localhost:8000)",
        )
        
        # MCP Health check
        if st.button("🔍 Check MCP Health", use_container_width=True):
            try:
                from agent.mcp_client import MCPClient
                
                mcp_client = MCPClient(mcp_url)
                is_healthy = mcp_client.health_check()
                
                if is_healthy:
                    st.session_state.mcp_health = True
                    st.success("✅ MCP server is healthy")
                else:
                    st.session_state.mcp_health = False
                    st.error("❌ MCP server is unavailable")
            
            except Exception as e:
                st.session_state.mcp_health = False
                st.error(f"❌ Error: {str(e)}")
        
        if st.session_state.mcp_health is not None:
            health_icon = "✅" if st.session_state.mcp_health else "❌"
            health_text = "Online" if st.session_state.mcp_health else "Offline"
            st.caption(f"{health_icon} MCP Server: {health_text}")
        
        st.divider()
        st.subheader("Agent Settings")
        
        # System prompt customization
        default_prompt = """You are a helpful AI assistant with access to tools that can fetch data from JSONPlaceholder API.

You have access to the following tools:
- get_post(post_id): Get a specific post
- list_posts(user_id=None): List all posts or posts by a user
- get_comments_for_post(post_id): Get comments on a post
- get_user(user_id): Get user information
- list_users(): List all users

Always use tools to provide accurate information. Be conversational and helpful."""
        
        system_prompt = st.text_area(
            "System Prompt",
            value=default_prompt,
            height=150,
            help="Customize the system prompt for the agent",
        )
        
        # Temperature and max tokens
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Lower = more focused, Higher = more creative",
            )
        
        with col2:
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=256,
                max_value=4096,
                value=2048,
                step=256,
            )
        
        st.divider()
        st.subheader("Conversation")
        
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.agent = None
            st.rerun()
        
        # Message count
        st.caption(f"Messages in conversation: {len(st.session_state.messages)}")
        
        st.divider()
        st.subheader("About")
        st.caption("**AI Agent v1.0**")
        st.caption("Powered by Streamlit + LLM + MCP")
        st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return {
            "llm_provider": provider,
            "llm_api_key": api_key,
            "llm_model": selected_model,
            "mcp_server_url": mcp_url,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }


def create_agent(config: dict) -> AgentOrchestrator:
    """Create or retrieve agent instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized AgentOrchestrator instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    if st.session_state.agent is not None:
        return st.session_state.agent
    
    if not config.get("llm_api_key"):
        raise ValueError("LLM API key is required. Set in .env or environment variables.")
    
    try:
        agent = AgentOrchestrator(
            llm_provider=config["llm_provider"],
            llm_api_key=config["llm_api_key"],
            llm_model=config["llm_model"],
            mcp_server_url=config["mcp_server_url"],
            system_prompt=config.get("system_prompt"),
        )
        
        st.session_state.agent = agent
        return agent
    
    except Exception as e:
        st.session_state.agent_error = str(e)
        raise


def render_messages() -> None:
    """Render conversation messages in the chat interface."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show tool calls if present
            if message.get("tool_calls"):
                with st.expander("🔧 Tool Calls"):
                    for tool_call in message["tool_calls"]:
                        st.markdown(f"**Tool:** `{tool_call['name']}`")
                        st.json(tool_call.get("arguments", {}))


def process_user_input(user_input: str, config: dict) -> None:
    """Process user input and generate agent response.
    
    Args:
        user_input: The user's message
        config: Configuration dictionary
    """
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Create agent if needed
    try:
        agent = create_agent(config)
    except Exception as e:
        st.error(f"❌ Failed to initialize agent: {str(e)}")
        st.session_state.messages.pop()  # Remove user message on error
        return
    
    # Process message with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Show thinking indicator
            with st.spinner("🤔 Thinking..."):
                # Stream the response
                for chunk in agent.stream_message(
                    user_input,
                    st.session_state.messages[:-1],  # Exclude current user message
                ):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
            
            # Final response
            message_placeholder.markdown(full_response)
            
            # Add assistant message to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "tool_calls": None,  # Would be populated if tool calls were made
            })
        
        except Exception as e:
            error_msg = f"❌ **Error:** {str(e)}"
            message_placeholder.markdown(error_msg)
            
            # Still add to history for context
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
            })


def main() -> None:
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Render main title
    st.title("🤖 AI Agent - JSONPlaceholder")
    st.markdown("""
    Chat with an AI agent that has access to JSONPlaceholder API tools.
    The agent can fetch posts, comments, users, and more!
    """)
    
    # Render sidebar
    config = render_sidebar()
    
    # Show configuration status
    if st.session_state.agent_error:
        st.error(f"⚠️ Agent Error: {st.session_state.agent_error}")
    
    # Render conversation
    render_messages()
    
    # Chat input
    if user_input := st.chat_input("Type your message here..."):
        process_user_input(user_input, config)


if __name__ == "__main__":
    main()
