"""
llmapi.py
Module for initialising the LLM connection via the Groq cloud API.
Reads credentials and model configuration from a .env file so that
no secrets are hard-coded in source.
"""

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# Load environment variables from the .env file located in the project root
load_dotenv()


def get_groqllm() -> ChatOpenAI:
    """Create and return a ChatOpenAI instance configured for the Groq API.

    Environment variables required in .env:
        GROQ_KEY      - API key from https://console.groq.com
        GROQ_ENDPOINT - Base URL for the Groq OpenAI-compatible endpoint
        GROQ_MODEL    - Model identifier (e.g. llama-3.3-70b-versatile)

    Returns:
        ChatOpenAI instance ready to be used by LangChain chains.
    """
    return ChatOpenAI(
        api_key=os.getenv("GROQ_KEY"),
        base_url=os.getenv("GROQ_ENDPOINT"),
        model=os.getenv("GROQ_MODEL"),
        temperature=0,
    )
