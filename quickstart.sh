#!/bin/bash
# Quick Start Script for JSONPlaceholder MCP Server + Streamlit Agent

echo "🚀 JSONPlaceholder MCP Server + Streamlit Agent"
echo "================================================"
echo ""

# Check Python version
echo "✓ Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION found"
echo ""

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "✓ Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installation Options:"
echo "1. Install MCP Server dependencies"
echo "2. Install Streamlit Agent dependencies"
echo "3. Install both"
echo ""

read -p "Choose (1-3): " choice

case $choice in
    1)
        echo "Installing MCP Server dependencies..."
        pip install -r requirements.txt
        echo "✓ MCP Server ready!"
        echo ""
        echo "To start MCP Server:"
        echo "  python -m app.main"
        ;;
    2)
        echo "Installing Streamlit Agent dependencies..."
        pip install -r streamlit_agent/requirements.txt
        echo "✓ Streamlit Agent ready!"
        echo ""
        echo "To configure Streamlit Agent:"
        echo "  cp streamlit_agent/.env.example streamlit_agent/.env"
        echo "  # Edit .env with your LLM API key"
        echo ""
        echo "To start Streamlit Agent:"
        echo "  streamlit run streamlit_agent/app.py"
        ;;
    3)
        echo "Installing all dependencies..."
        pip install -r requirements.txt
        pip install -r streamlit_agent/requirements.txt
        echo "✓ Everything ready!"
        echo ""
        echo "To start MCP Server (Terminal 1):"
        echo "  python -m app.main"
        echo ""
        echo "To start Streamlit Agent (Terminal 2):"
        echo "  cp streamlit_agent/.env.example streamlit_agent/.env"
        echo "  # Edit .env with your LLM API key"
        echo "  streamlit run streamlit_agent/app.py"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "For more information, see WORKSPACE.md"
