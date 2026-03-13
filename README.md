py -0
py -3.13 -m venv .venv

pip install -r requirements.txt

pip install pandas langchain langchain_huggingface langchain_community PyPDF2 langchain_openai dotenv groq sentence-transformers langchain-chroma


langchain.text_splitter -> langchain_text_splitters

Uses
Python 3.12
Poetry 2.2.0
VS code


How to run


A. you need an OPENAI_API_KEY from   https://platform.openai.com/api-keys

B. Open a terminal using Command Line and execute

poetry install

1. select the venv
2. change in pyproject.toml the  requires-python = ">=3.12, <4.0.0"

poetry add pandas langchain langchain_huggingface langchain_community PyPDF2 langchain_openai openai dotenv sentence-transformers langchain-chroma

 
