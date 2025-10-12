""""
llmapi.py
library to load llms
source 01.01
"""

from langchain_openai import AzureChatOpenAI, ChatOpenAI
 
from openai import AzureOpenAI, OpenAI

from dotenv import load_dotenv
import os
 
# Load environment variables from the .env file
load_dotenv()

def getAzureLLM() -> AzureChatOpenAI:
    """Initialize the Azure OpenAI chat model."""
    return AzureChatOpenAI(
        azure_endpoint=  os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment= os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        model= os.getenv("AZURE_OPENAI_MODEL"),
        api_key = os.getenv("AZURE_OPENAI_API_KEY") ,
        temperature=0
    )


def getAzureOnly() -> AzureOpenAI:
    """Initialize the Azure OpenAI chat model."""
    return AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint= os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )

def getAzureEmbedDeployment() -> str:
    return os.getenv("AZURE_EMBED_DEPLOYMENT_NAME")


def getOpenLLM() -> ChatOpenAI:
    """Create a standard OpenAI Chat model instance."""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),  # default to gpt-4o
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=200
    )

def getOpenOnly() -> OpenAI:
    """Create a standard OpenAI Chat model instance."""
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    ) 

# -------------------------
# Run Example
# -------------------------
if __name__ == "__main__":

    # llm = getAzureLLM()
    # response = llm.invoke("What is the capital of France?")
    # print(response.content)
 
    # llm = getOpenLLM()
    # response = llm.invoke("What is the capital of France?")
    # print(response.content)


    # llm = getAzureLLM()
    # response = llm.invoke([HumanMessage(content="What is the capital of France?")])
    # print(response.content)
 
    # llm = getOpenLLM()
    # response = llm.invoke([HumanMessage(content="What is the capital of France?")])
    # print(response.content)

    client = getAzureOnly()
 
