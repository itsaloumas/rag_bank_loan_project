""""
llmapi.py
library to load llms
source 01.01
"""

from langchain_openai import ChatOpenAI
from groq import Groq
from dotenv import load_dotenv
import os
 
# Load environment variables from the .env file
load_dotenv()


def get_groqllm()->ChatOpenAI:
    return ChatOpenAI(
    api_key=os.getenv("GROQ_KEY"),
    base_url=os.getenv("GROQ_ENDPOINT"),
    model=os.getenv("GROQ_MODEL"),
    temperature=0,
    )

def get_openllm()->ChatOpenAI:
    return  ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
    )
