import os
import requests
import hashlib
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pinecone import Pinecone
from pinecone import ServerlessSpec

# Load environment variables
load_dotenv()

# Set API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("INDEX_NAME")

if not OPENAI_API_KEY or not OMDB_API_KEY or not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
    raise ValueError("Please set all API keys and Pinecone index name in your .env file.")

# Initialize OpenAI model & embeddings
llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)
embed_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Ensure correct index exists
existing_indexes = pc.list_indexes().names()
if PINECONE_INDEX_NAME in existing_indexes:
    index_info = pc.describe_index(PINECONE_INDEX_NAME)
    if index_info.dimension != 1536:
        print(f"Deleting existing index '{PINECONE_INDEX_NAME}' due to incorrect dimensions ({index_info.dimension}).")
        pc.delete_index(PINECONE_INDEX_NAME)

# Create the index with correct dimensions
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  
    )

index = pc.Index(PINECONE_INDEX_NAME)

# Function to generate embeddings
def get_embedding(text):
    """Generate an embedding for the given text using OpenAI's Embeddings API."""
    return embed_model.embed_query(text)

# Function to check Pinecone before querying OMDb
def search_media(title, media_type="movie"):
    """Fetches movie or TV show details from Pinecone if available, otherwise queries OMDb."""
    
    # Generate a unique ID based on media type and title
    doc_id = f"{media_type}_{title.lower()}"

    # Generate embedding for the search query
    query_embedding = get_embedding(title)

    # Search for similar entries in Pinecone with correct media type and title
    query_result = index.query(
        vector=query_embedding, 
        top_k=1, 
        include_metadata=True, 
        filter={"id": doc_id}  # Ensures correct media type & title match
    )

    if query_result and query_result.matches:
        match = query_result.matches[0]
        if match.score > 0.85:
            print("\nRetrieved from Pinecone cache.\n")
            return match.metadata  # Return stored metadata

    # If not found, fetch from OMDb
    url = f"http://www.omdbapi.com/?t={title}&type={media_type}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            media_details = {
                "Title": data.get("Title"),
                "Year": data.get("Year"),
                "Director": data.get("Director", "N/A"),
                "Cast": data.get("Actors", "N/A"),
                "IMDB Rating": data.get("imdbRating", "N/A"),
                "Genre": data.get("Genre", "N/A"),
                "Seasons": data.get("totalSeasons") if media_type == "series" else "N/A",
                "Plot": data.get("Plot", "N/A"),
                "Trailer": f"https://www.youtube.com/results?search_query={title}+trailer"
            }

            # Store result in Pinecone
            index.upsert(vectors=[(doc_id, query_embedding, media_details)])
            print("\nStored in Pinecone for future retrieval.\n")

            return media_details
        else:
            return {"Error": "Media not found. Check the title and try again."}
    
    return {"Error": "Failed to retrieve data. Please try again later."}

# Test the agent
if __name__ == "__main__":
    media_type = input("Enter 'movie' or 'series': ").strip().lower()
    user_query = input("Enter the title: ").strip()
    
    result = search_media(user_query, media_type)
    print("\nAgent Response:\n", result)
