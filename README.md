# RAG-Agent-for-Movie-and-Series-Search

## Overview
This project is a Tkinter-based desktop application that allows users to search for movies and TV series. It integrates OMDb API, OpenAI (GPT-4), Pinecone, DuckDuckGo, and YouTube to retrieve and display detailed information, including trailers and related links.

## Technologoes and frameworks used
•Python (Primary programming language)

•Tkinter (For GUI development)

•LangChain (For OpenAI LLM integration)

•Pinecone (For vector database storage and retrieval)

•OMDb API (For fetching movie and TV series details)

•DuckDuckGo Search API (For fetching related web links)

•YouTube Search API (For fetching trailers)

•Requests & Hashlib (For API requests and data hashing)

•dotenv (For managing environment variables)


## Features

•Search Movies/TV Shows: Fetch details such as title, cast, director, genre, IMDb rating, plot, and trailer links.

•Cache Results with Pinecone: Avoids redundant API calls by storing and retrieving search results.

•YouTube Trailer Fetching: Retrieves up to 5 trailers for the searched movie/series.

•DuckDuckGo Integration: Provides additional related links.

•Interactive GUI: Users can search and click links directly from the interface.


## Installation & Setup

1. Clone the repository:

'''git clone https://github.com/your-repo/movie-search-app.git
cd movie-search-app

2. Install dependencies:

pip install -r requirements.txt

3. Create a .env file and add API keys:

OPENAI_API_KEY=your_openai_api_key
OMDB_API_KEY=your_omdb_api_key
PINECONE_API_KEY=your_pinecone_api_key
INDEX_NAME=your_pinecone_index

4. Run the application:
  python app.py

python app.py




